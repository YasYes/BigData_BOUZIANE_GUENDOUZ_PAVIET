package fr.cytech.integration

import org.apache.spark.sql.{SparkSession, DataFrame}

object SparkApp extends App {

  // Initialisation de la session avec la configuration S3A intégrée
  val spark = SparkSession.builder()
    .appName("SparkApp")
    .master("local[*]")
    .config("fs.s3a.access.key", "minio")
    .config("fs.s3a.secret.key", "minio123")
    .config("fs.s3a.endpoint", "http://minio:9000/")
    .config("fs.s3a.path.style.access", "true")
    .config("fs.s3a.connection.ssl.enable", "false")
    .config("fs.s3a.attempts.maximum", "1")
    .config("fs.s3a.connection.establish.timeout", "6000")
    .config("fs.s3a.connection.timeout", "5000")
    .config("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .getOrCreate()

  spark.sparkContext.setLogLevel("WARN")

  // Définition des variables de chemin
  val fileName = "yellow_tripdata_2025-11.parquet"
  val localPath = s"data/raw/$fileName"
  val minioPath = s"s3a://nyc-raw/$fileName"

  try {
    println(s"Démarrage de l'intégration : $localPath")

    // Lecture du fichier local
    val df: DataFrame = spark.read.parquet(localPath)

    // Écriture vers le bucket Minio
    println(s"Transfert vers Minio : $minioPath")
    df.write
      .mode("overwrite")
      .parquet(minioPath)

    println("Succès : Les données ont été injectées dans le Data Lake.")

  } catch {
    case e: Exception =>
      println(s"Erreur critique durant l'exécution : ${e.getMessage}")
      e.printStackTrace()
  } finally {
    // Fermeture propre de la session
    spark.stop()
  }
}