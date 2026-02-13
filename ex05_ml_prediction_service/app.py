import streamlit as st
import pandas as pd
import joblib
import json
import os
from sqlalchemy import create_engine
from datetime import datetime

# --- CONFIGURATION ET CHARGEMENT ---


@st.cache_data
def get_zone_mapping():
    """
    Récupère la table de correspondance des zones depuis PostgreSQL.

    Cette fonction interroge la table 'Taxi_Zone' pour créer un dictionnaire
    permettant de traduire le nom d'une zone en son ID numérique.
    En cas d'échec de connexion, une liste par défaut est utilisée.

    Returns
    -------
    dict
        Un dictionnaire où les clés sont les noms des zones (str) et les
        valeurs sont les IDs (int).
    """
    engine = create_engine('postgresql://cytech:'
                           'password@postgres:5432/postgres')
    try:
        # On interroge la table de dimension
        query = "SELECT zone_id, name FROM Taxi_Zone ORDER BY name"
        df_zones = pd.read_sql(query, engine)
        if not df_zones.empty:
            return pd.Series(df_zones.zone_id.values,
                             index=df_zones.name).to_dict()
    except Exception:
        pass

        # Fallback si la DB est inaccessible ou vide
    return {"JFK Airport": 132, "LaGuardia Airport": 138, "Times Square": 230}


def load_metrics():
    """
    Charge le score de performance (RMSE) du modèle.

    Lit le fichier 'model_metrics.json' généré lors de l'entraînement
    pour afficher la précision du modèle à l'utilisateur.

    Returns
    -------
    str
        Le RMSE formaté (ex: "5.42 $") ou un message d'erreur/N/A.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    metrics_path = os.path.join(current_dir, 'model_metrics.json')

    try:
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                data = json.load(f)
                return f"{data['rmse']:.2f} $"
        return "N/A"
    except Exception:
        return "Erreur JSON"


@st.cache_data
def get_distance_stats(pu_id, do_id):
    """
    Interroge la base pour obtenir les statistiques
    de distance pour un trajet donné.

    Permet de proposer une distance par défaut intelligente à l'utilisateur
    en se basant sur l'historique des trajets entre ces deux zones.

    Parameters
    ----------
    pu_id : int
        L'identifiant de la zone de départ (Pickup Location ID).
    do_id : int
        L'identifiant de la zone d'arrivée (Dropoff Location ID).

    Returns
    -------
    tuple
        Un tuple contenant trois flottants :
        (min_distance, max_distance, avg_distance).
        Renvoie des valeurs par défaut en cas d'erreur ou d'absence de données.
    """
    engine = create_engine('postgresql://cytech:'
                           'password@localhost:5432/postgres')
    query = f"""
        SELECT MIN(trip_distance) as min_d, MAX(trip_distance)
        as max_d, AVG(trip_distance) as avg_d
        FROM fact_taxi_trips
        WHERE pu_location_id = {pu_id} AND do_location_id = {do_id}
    """
    try:
        df = pd.read_sql(query, engine)
        if df['min_d'].iloc[0] is not None:
            return (round(float(df['min_d'].iloc[0]), 2),
                    round(float(df['max_d'].iloc[0]), 2),
                    round(float(df['avg_d'].iloc[0]), 2))
    except Exception:
        pass
    return 0.1, 50.0, 2.5   # Valeurs par défaut si aucun historique

# --- INTERFACE PRINCIPALE ---


def main():
    """
    Fonction principale de l'application Streamlit.

    Orchestre l'affichage de l'interface utilisateur :
    1. Chargement des données (Zones, Modèle).
    2. Création des widgets de formulaire (Sélection zones, date, distance).
    3. Appel au modèle de Machine Learning pour la prédiction.
    4. Affichage du résultat et des détails.
    """

    st.set_page_config(page_title="NYC Taxi Expert",
                       layout="wide", page_icon="🚖")

    # Chargement des ressources
    zones_dict = get_zone_mapping()

    try:
        # Chargement du modèle entraîné à l'Exercice 5
        model = joblib.load('/opt/airflow/ml_scripts/taxi_model.joblib')
    except FileNotFoundError:
        st.error("Modèle 'taxi_model.joblib' introuvable."
                 " Lancez d'abord train.py.")
        return

    st.title("NYC Taxi : Estimateur de Prix de Production")
    st.write("---")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.header("Configuration du trajet")

        # 1. Sélection des lieux
        pu_name = st.selectbox("Zone de départ",
                               options=list(zones_dict.keys()))
        do_name = st.selectbox("Zone d'arrivée",
                               options=list(zones_dict.keys()))

        # 2. Récupération des IDs et des statistiques
        pu_id = zones_dict[pu_name]
        do_id = zones_dict[do_name]
        min_d, max_d, avg_d = get_distance_stats(pu_id, do_id)

        # 3. Information contextuelle et distance dynamique
        st.caption(f"Historique trajet : min **{min_d}** mi"
                   f" | max **{max_d}** mi")
        dist = st.number_input(
            "Distance estimée (miles)",
            min_value=0.0,
            max_value=float(max_d + 15.0),
            value=float(avg_d),
            step=0.1,
            help="Initialisé à la moyenne historique pour ce trajet."
        )

        # 4. Temporel
        st.write("**Date et Heure du trajet**")
        d = st.date_input("Date", datetime.now())
        t = st.time_input("Heure", datetime.now())

        combined_dt = datetime.combine(d, t)
        selected_hour = combined_dt.hour
        selected_day = combined_dt.weekday()   # 0=Lundi
        day_name = combined_dt.strftime("%A")

        passengers = st.slider("Nombre de passagers", 1, 6, 1)

    with col2:
        st.header("Prédiction ")

        if st.button("Calculer le prix estimé"):
            # préparation des features
            input_data = pd.DataFrame({
                'trip_distance': [dist],
                'pu_location_id': [pu_id],
                'do_location_id': [do_id],
                'passenger_count': [passengers],
                'pickup_hour': [selected_hour],
                'pickup_day_of_week': [selected_day]
            })

            with st.spinner('Analyse en cours...'):
                try:
                    prediction = model.predict(input_data)[0]

                    st.success(f"### Prix estimé : **{prediction:.2f} $**")

                    if dist < min_d or dist > max_d:
                        st.warning(f" Distance atypique : L'historique "
                                   f"pour ce trajet est entre {min_d} "
                                   f"et {max_d} miles.")

                    st.info(f"""
                    **Détails du calcul :**
                    - Départ : {pu_name} | Arrivée : {do_name}
                    - Moment : {day_name} à {selected_hour}h
                    """)
                except Exception as e:
                    st.error(f"Erreur d'inférence : {e}")

    st.write("---")
    st.caption("Projet Big Data - CY Tech ")


if __name__ == "__main__":
    main()
