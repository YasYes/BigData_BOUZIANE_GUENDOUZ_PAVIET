import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime


def predict_price(distance, pu_loc, do_loc, passengers=1, pickup_time=None):
    """
    Predit le prix d'une course de taxi en incluant les variables temporelles.

    Cette fonction charge le modèle entraîné, calcule les features temporelles
    (heure, jour de la semaine) et retourne une estimation.

    Parameters
    ----------
    distance : float
        La distance du trajet en miles.
    pu_loc : int
        L'identifiant de la zone de départ (Pickup Location ID).
    do_loc : int
        L'identifiant de la zone d'arrivée (Dropoff Location ID).
    passengers : int, optional
        Le nombre de passagers (Default value = 1).
    pickup_time : str or datetime, optional
        La date et l'heure de la course (ex: "2024-06-15 14:30:00").
        Si non fourni (None), utilise l'heure actuelle (Default value = None).

    Returns
    -------
    float
        Le prix estimé de la course en dollars (arrondi à 2 décimales).
    """

    # Gestion du modèle
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'taxi_model.joblib')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle introuvable : {model_path}")

    model = joblib.load(model_path)

    # Feature engineering
    # Si aucune heure n'est fournie, on utilise l'heure actuelle
    if pickup_time is None:
        dt = datetime.now()
    else:
        dt = pd.to_datetime(pickup_time)

    hour = dt.hour
    day_of_week = dt.weekday()   # 0=Lundi, 6=Dimanche

    # Création du DataFrame avec les 6 colonnes requises
    input_data = pd.DataFrame({
        'trip_distance': [distance],
        'pu_location_id': [pu_loc],
        'do_location_id': [do_loc],
        'passenger_count': [passengers],
        'pickup_hour': [hour],             # Ajouté pour la cohérence
        'pickup_day_of_week': [day_of_week]  # Ajouté pour la cohérence
    })

    # Prédiction
    try:
        # On s'assure que l'ordre des colonnes est le
        # même que lors de l'entraînement
        prediction = model.predict(input_data)[0]
        return np.round(prediction, 2)
    except Exception as e:
        print(f"Erreur lors de la prédiction : {e}")
        return 0.0


if __name__ == "__main__":
    print("--- Test de prédiction (Coherent avec l'entraînement) ---")

    # Test 1 : Maintenant
    prix_now = predict_price(2.5, 161, 237)
    print(f"Estimation (Départ immédiat) : {prix_now} $")

    # Test 2 : Simulation un Samedi soir à 23h (potentiellement plus cher)
    prix_weekend = predict_price(2.5, 161, 237,
                                 pickup_time="2026-01-31 23:00:00")
    print(f"Estimation (Samedi soir 23h) : {prix_weekend} $")
