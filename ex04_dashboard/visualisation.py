import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os

# --- CONFIGURATION ---
# Connexion avec nos identifiants
engine = create_engine('postgresql://cytech:password@postgres:5432/postgres')
dossier_sortie = "/opt/airflow/reports/figures/"
if not os.path.exists(dossier_sortie):
    os.makedirs(dossier_sortie)

# On définit un style propre pour les graphiques
sns.set_theme(style="whitegrid")

print("--- Démarrage de la génération des graphiques ---")

# GRAPHIQUE 1 : Analyse Géographique
print("1. Génération du graphique par Arrondissement...")
query_geo = """
            SELECT B.name as arrondissement, COUNT(F.trip_id) as nombre_courses
            FROM Fact_Taxi_Trips F
                     JOIN Taxi_Zone Z ON F.pu_location_id = Z.zone_id
                     JOIN Borough B ON Z.borough_id = B.borough_id
            GROUP BY B.name ORDER BY nombre_courses DESC; \
            """
df_geo = pd.read_sql(query_geo, engine)

plt.figure(figsize=(10, 6))
sns.barplot(data=df_geo, x='arrondissement', y='nombre_courses',
            hue='arrondissement', palette='viridis', legend=False)
plt.title('Volume de courses par Arrondissement')
plt.xlabel('Arrondissement')
plt.ylabel('Nombre de courses')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{dossier_sortie}1_repartition_geographique.png")
plt.close()

# GRAPHIQUE 2 : Analyse Financière

print("2. Génération du graphique des prix...")
# On regarde la distribution des prix
# (en filtrant les valeurs aberrantes > 100$)
query_prix = """
             SELECT total_amount FROM Fact_Taxi_Trips
             WHERE total_amount > 0 AND total_amount < 200;
               \
             """
df_prix = pd.read_sql(query_prix, engine)

plt.figure(figsize=(10, 6))
sns.histplot(df_prix['total_amount'], bins=50, kde=True, color='green')
plt.title('Distribution du prix des courses (Target ML)')
plt.xlabel('Prix ($)')
plt.ylabel('Fréquence')
plt.tight_layout()
plt.savefig(f"{dossier_sortie}2_distribution_prix.png")
plt.close()

# GRAPHIQUE 3 : Analyse Temporelle
print("3. Génération du graphique temporel...")
# On extrait l'heure de la course
query_time = """
             SELECT EXTRACT(HOUR FROM pickup_datetime)
                        as heure, COUNT(*) as nombre
             FROM Fact_Taxi_Trips
             GROUP BY heure ORDER BY heure; \
             """
df_time = pd.read_sql(query_time, engine)

plt.figure(figsize=(10, 6))
sns.lineplot(data=df_time, x='heure', y='nombre', marker='o', color='red')
plt.title('Affluence des taxis par heure de la journée')
plt.xlabel('Heure (0-23)')
plt.ylabel('Nombre de courses')
plt.xticks(range(0, 24))
plt.grid(True)
plt.tight_layout()
plt.savefig(f"{dossier_sortie}3_pic_activite.png")
plt.close()

print(f"TERMINÉ ! Les 3 images sont dans le dossier {dossier_sortie}")
