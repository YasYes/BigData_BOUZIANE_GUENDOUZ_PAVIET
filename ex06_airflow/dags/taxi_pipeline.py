from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime
import os


def read_sql_file(file_path):
    """
    Lit le contenu d'un fichier SQL.

    :param file_path: Chemin vers le fichier SQL.
    :return: Contenu texte du fichier.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier SQL introuvable : {file_path}")
    with open(file_path, 'r') as f:
        return f.read()


with DAG(
        'nyc_taxi_full_pipeline',
        start_date=datetime(2026, 1, 1),
        schedule_interval=None,
        catchup=False,
        tags=['cytech', 'big_data', 'exercice_final']
) as dag:

    # -Infrastructure
    create_raw = S3CreateBucketOperator(
        task_id='setup_nyc_raw',
        bucket_name='nyc-raw',
        aws_conn_id='minio_conn',
        region_name='us-east-1'
    )

    create_silver = S3CreateBucketOperator(
        task_id='setup_nyc_silver',
        bucket_name='nyc-silver',
        aws_conn_id='minio_conn',
        region_name='us-east-1'
    )

    # Exo 3
    setup_tables = SQLExecuteQueryOperator(
        task_id='setup_sql_tables',
        conn_id='postgres_default',
        sql=read_sql_file('/opt/airflow/ex03_sql_table_creation/creation.sql'),
    )

    setup_insertion = SQLExecuteQueryOperator(
        task_id='insert_reference_data',
        conn_id='postgres_default',
        sql=read_sql_file('/opt/airflow/ex03_sql_table_creation/insertion.sql'),
    )

    # Exo 1 & 2
    t1_integration = BashOperator(
        task_id='integration_raw',
        bash_command='spark-submit --class fr.cytech.integration.SparkApp '
                     '/opt/airflow/jars/integration.jar',
        cwd='/opt/airflow'
    )

    t2_sync = BashOperator(
        task_id='sync_sql',
        bash_command='spark-submit --class fr.cytech.integration.SparkApp '
                     '/opt/airflow/jars/sync_sql.jar'
    )

    # Vérification PEP 8
    check_pep8 = BashOperator(
        task_id='check_pep8_compliance',
        bash_command='flake8 /opt/airflow/ml_scripts/'
    )

    # Vérification documentation NumpyDoc via pyment
    check_docs = BashOperator(
        task_id='check_documentation',
        bash_command='pyment -v /opt/airflow/ml_scripts/cd'
    )

    # Tests unitaires sur les données
    run_unit_tests = BashOperator(
        task_id='run_unit_tests',
        bash_command='pytest /opt/airflow/ml_scripts/test_model.py'
    )

    # Exo 4 & 5
    t4_viz = BashOperator(
        task_id='generate_visualisations',
        bash_command='python3 /opt/airflow/ex04_dashboard/visualisation.py'
    )

    t3_train = BashOperator(
        task_id='train_model',
        bash_command='python3 /opt/airflow/ml_scripts/train.py'
    )



    # Dépendances
    # 1. Mise en place de l'infra et des données
    [create_raw, create_silver] >> setup_tables >> setup_insertion
    setup_insertion >> t1_integration >> t2_sync

    # 2. Une fois les données prêtes, on lance :
    #    - La visualisation (t4_viz)
    #    - Les vérifications de style de code (check_pep8, check_docs)
    #    - L'entraînement du modèle (t3_train)
    #    Note : On lance l'entraînement AVANT les tests unitaires
    t2_sync >> [t4_viz, check_pep8, check_docs, t3_train]

    # 3. Les tests unitaires ne se lancent QUE si l'entraînement est fini
    #    (Car les tests ont besoin du fichier .joblib généré par t3_train)
    t3_train >> run_unit_tests