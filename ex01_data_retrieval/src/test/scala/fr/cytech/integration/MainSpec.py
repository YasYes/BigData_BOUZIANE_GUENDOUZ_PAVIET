import os
import requests

def test_raw_data_exists():
    file_name = "yellow_tripdata_2025-11.parquet"
    file_path = os.path.join("data", "raw", file_name)

    if os.path.exists(file_path):
        print(f"Test Fichier : {file_path} est présent.")
        return True
    else:
        print(f"Test Fichier : {file_path} est introuvable. Lancez le script de collecte d'abord.")
        return False

def test_minio_connectivity():
    try:
        # On vérifie l'accès à l'API de Minio
        response = requests.get("http://localhost:9000/minio/health/live", timeout=5)
        if response.status_code == 200:
            print("Test Connectivité : Minio est en ligne.")
            return True
        else:
            print(f"Test Connectivité : Minio répond avec le code {response.status_code}.")
            return False
    except Exception as e:
        print(f"Test Connectivité : Impossible de joindre Minio. Vérifiez que Docker est lancé.")
        return False

if __name__ == "__main__":
    print("Début du test de couverture (EXERCICE 1)")

    # Exécution des tests
    results = [test_raw_data_exists(), test_minio_connectivity()]

    if all(results):
        print("\nBILAN : Tous les tests de l'Exercice 1 sont validés.")
        exit(0)
    else:
        print("\nBILAN : Des erreurs ont été détectées.")
        exit(1)