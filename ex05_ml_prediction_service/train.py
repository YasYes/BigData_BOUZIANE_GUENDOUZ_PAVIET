import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib
from tqdm import tqdm
import os

# Configuration Minio
MINIO_CONF = {
    "client_kwargs": {
        "endpoint_url": "http://minio:9000",
        "aws_access_key_id": "minio",
        "aws_secret_access_key": "minio123"
    }
}


def load_data_from_minio(bucket_path):
    """
    Charge les données depuis un fichier Parquet stocké sur Minio.

    Parameters
    ----------
    bucket_path : str
        Le chemin complet S3 du fichier à c

    Returns
    -------
    pd.DataFrame
        Un DataFrame Pandas contenant les données de courses de taxi.
    """
    print(f"Tentative de chargement depuis {bucket_path}...")
    return pd.read_parquet(bucket_path, storage_options=MINIO_CONF)


def train_model():
    """
    Exécute le pipeline complet d'entraînement du modèle (MLOps).

    Cette fonction orchestre les étapes suivantes :
    1. Chargement des données depuis le Data Lake.
    2. Feature Engineering : Extraction de l'heure et du jour de la semaine.
    3. Nettoyage : Suppression des valeurs manquantes et filtrage des outliers.
    4. Entraînement : Random Forest Regressor avec barre de progression.
    5. Évaluation : Calcul et affichage du RMSE.
    6. Sauvegarde : Export du modèle au format .joblib.
    """
    # Chargement
    file_path = 's3://nyc-silver/yellow_tripdata_cleaned.parquet'
    try:
        df = load_data_from_minio(file_path)
        print("Fichier chargé avec succès !")
    except Exception as e:
        print(f"Erreur critique : {e}")
        return

    # Feature engineering (Temporel)
    print("Extraction des caractéristiques temporelles...")

    # Conversion en datetime
    df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])

    # Extraction de l'heure et du jour de la semaine
    df['pickup_hour'] = df['pickup_datetime'].dt.hour
    df['pickup_day_of_week'] = df['pickup_datetime'].dt.dayofweek

    # Nettoyage
    # Ajout des nouvelles colonnes à la liste des features
    features = [
        'trip_distance',
        'pu_location_id',
        'do_location_id',
        'passenger_count',
        'pickup_hour',
        'pickup_day_of_week'
    ]
    target = 'total_amount'

    df = df.dropna(subset=features + [target])

    # Filtres de qualité (Prix entre 2.5 et 80$, distance raisonnable)
    df = df[(df[target] >= 2.5) & (df[target] <= 200)]
    df = df[(df['trip_distance'] > 0.1) & (df['trip_distance'] < 200)]

    print(f"Taille du dataset après engineering : {len(df)} lignes")

    X = df[features]
    y = df[target]

    # Split Train/Test
    X_train, X_test, y_train, y_test \
        = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraînement
    print("\nDémarrage de l'entraînement du Random Forest...")
    n_estimators = 50

    model = RandomForestRegressor(
        n_estimators=0,
        warm_start=True,
        max_depth=12,
        n_jobs=-1,
        random_state=42
    )

    with tqdm(total=n_estimators,
              desc="Progression de la Forêt", unit="arbre") as pbar:
        for i in range(n_estimators):
            model.n_estimators += 1
            model.fit(X_train, y_train)
            pbar.update(1)

    # Évaluation
    print("\nÉvaluation du modèle...")
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print("--- RÉSULTATS ---")
    print(f"RMSE atteint : {rmse:.2f} ")

    # Sauvegarde
    os.makedirs(os.path.dirname('/opt/airflow/ml_scripts/taxi_model.joblib'),
                exist_ok=True)
    joblib.dump(model, '/opt/airflow/ml_scripts/taxi_model.joblib')
    print("Modèle sauvegardé sous 'taxi_model.joblib'")


if __name__ == "__main__":
    train_model()
