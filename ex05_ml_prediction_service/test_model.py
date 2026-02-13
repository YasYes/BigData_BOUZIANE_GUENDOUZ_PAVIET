import pytest
import os
import numpy as np
from predict import predict_price

# Configuration des chemins
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(CURRENT_DIR, 'taxi_model.joblib')

# Test 1 : Infrastructure


def test_model_file_exists():
    """
    Vérifie la présence physique du fichier modèle (.joblib).

    Ce test s'assure que le script d'entraînement (train.py) a bien été exécuté
    et que le fichier de sauvegarde est accessible pour l'inférence.
    """

    print("\n[Test 1] le fichier .joblib est pré")

    assert os.path.exists(MODEL_PATH), f"Modèle introuvable : {MODEL_PATH}"

# Test 2 : Logique Métier


def test_prediction_coherence():
    """
    Vérifie la cohérence du type et du signe de la prédiction.

    Le modèle doit retourner un nombre flottant strictement positif
    pour une course standard.
    """

    # Test à une date fixe pour la reproductibilité
    test_date = "2026-01-27 12:00:00"
    prix = predict_price(distance=2.5, pu_loc=161,
                         do_loc=237, pickup_time=test_date)

    print(f"[Test 2] Prix pour 2.5 miles le midi : {prix}$")

    assert prix > 0, "Le prix doit être positif"
    assert isinstance(prix, (float, np.float64, np.float32)), \
        "Le retour doit être un float"

# Test 3 : Distance


def test_price_variation_distance():
    """
    Vérifie la logique métier liée à la distance.

    Une course longue (10 miles) doit coûter plus cher qu'une course courte
    (1 mile) si les autres paramètres (heure, lieux) restent identiques.
    """

    date_fixe = "2026-01-27 10:00:00"
    prix_court = predict_price(1.0, 161, 162, pickup_time=date_fixe)
    prix_long = predict_price(10.0, 161, 162, pickup_time=date_fixe)

    print(f"[Test 3 ] Distance : 10 miles ({prix_long}$) "
          f"> 1 mile ({prix_court}$)")
    assert prix_long > prix_court

# Test 4 : Validations Temporelles


def test_temporal_impact():
    """
    Vérifie que le modèle est sensible aux variations temporelles.

    Le prix prédit pour une même course doit varier selon l'heure ,
    validant ainsi l'utilisation de la feature 'pickup_hour'.
    """
    dist, pu, do = 5.0, 161, 237

    # Simulation Lundi à 3h du matin
    prix_nuit = predict_price(dist, pu, do, pickup_time="2026-01-26 03:00:00")
    # Simulation Lundi à 18h (heure de pointe / trafic)
    prix_pointe = predict_price(dist, pu, do,
                                pickup_time="2026-01-26 18:00:00")

    print(f" [Test 4] Impact Temporel : Nuit ({prix_nuit}$) "
          f"vs Pointe ({prix_pointe}$)")

    # On vérifie que les prix ne sont pas identiques
    assert prix_nuit != prix_pointe, \
        "Le modèle devrait différencier le prix selon l'heure"

# Test 5 : Robustesse


def test_input_handling_types():
    """
    Vérifie la robustesse de la fonction de prédiction face aux types d'entrée.

    La fonction doit accepter des entiers (int)
    pour les paramètres qui attendent
    théoriquement des flottants (float), sans provoquer d'erreur d'exécution.
    """
    try:
        # Passage d'entiers pour la distance et IDs
        prix = predict_price(5, 100, 100, 1)
        assert prix >= 0
        print("[Test 5] Types d'entrées robustes.")
    except Exception as e:
        pytest.fail(f"Le script a crashé avec des entrées valides : {e}")


test_model_file_exists()
test_prediction_coherence()
test_price_variation_distance()
test_temporal_impact()
test_input_handling_types()
