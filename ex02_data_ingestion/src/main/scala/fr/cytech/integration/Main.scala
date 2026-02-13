package fr.cytech.integration

import org.apache.spark.sql.{SparkSession, DataFrame, SaveMode}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import java.util.Properties

object SparkApp extends App {

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

  try {
    // Lecture depuis la couche RAW
    println("Lecture des données RAW depuis Minio...")
    val rawDf = spark.read.parquet("s3a://nyc-raw/yellow_tripdata_2025-11.parquet")

    // Nettoyage, Typage et Renommage
    // On transforme le schéma pour qu'il soit identique à la table PostgreSQL
    val cleanedDf: DataFrame = rawDf
      .withColumn("vendor_id", col("VendorID").cast(IntegerType))
      .withColumn("pickup_datetime", col("tpep_pickup_datetime").cast(TimestampType))
      .withColumn("dropoff_datetime", col("tpep_dropoff_datetime").cast(TimestampType))
      .withColumn("passenger_count", col("passenger_count").cast(IntegerType))
      .withColumn("trip_distance", col("trip_distance").cast(DoubleType))
      .withColumn("rate_code_id", col("RatecodeID").cast(IntegerType))
      .withColumn("pu_location_id", col("PULocationID").cast(IntegerType))
      .withColumn("do_location_id", col("DOLocationID").cast(IntegerType))
      .withColumn("payment_type_id", col("payment_type").cast(IntegerType))
      .withColumn("fare_amount", col("fare_amount").cast(DoubleType))
      .withColumn("extra", col("extra").cast(DoubleType))
      .withColumn("mta_tax", col("mta_tax").cast(DoubleType))
      .withColumn("tip_amount", col("tip_amount").cast(DoubleType))
      .withColumn("tolls_amount", col("tolls_amount").cast(DoubleType))
      .withColumn("improvement_surcharge", col("improvement_surcharge").cast(DoubleType))
      .withColumn("total_amount", col("total_amount").cast(DoubleType))
      .withColumn("congestion_surcharge", col("congestion_surcharge").cast(DoubleType))
      .select(
        "vendor_id", "pickup_datetime", "dropoff_datetime", "passenger_count",
        "trip_distance", "rate_code_id", "pu_location_id", "do_location_id",
        "payment_type_id", "fare_amount", "extra", "mta_tax", "tip_amount",
        "tolls_amount", "improvement_surcharge", "total_amount", "congestion_surcharge"
      )
      .filter(col("trip_distance") > 0 && col("total_amount") > 0)

    // Minio (Couche Silver)
    println("Sauvegarde de la couche Silver Minio...")
    cleanedDf.write
      .mode(SaveMode.Overwrite)
      .parquet("s3a://nyc-silver/yellow_tripdata_cleaned.parquet")

    // PostgreSQL
    println("Ingestion vers PostgreSQL...")
    val jdbcUrl = "jdbc:postgresql://postgres:5432/postgres"
    val props = new Properties()
    props.setProperty("user", "cytech")
    props.setProperty("password", "password")
    props.setProperty("driver", "org.postgresql.Driver")

    cleanedDf.write
      .mode(SaveMode.Append)
      .jdbc(jdbcUrl, "Fact_Taxi_Trips", props)

    println("Synchronisation terminée avec succès !")

  } catch {
    case e: Exception =>
      println(s"Erreur lors du processing : ${e.getMessage}")
      e.printStackTrace()
  } finally {
    spark.stop()
  }
}