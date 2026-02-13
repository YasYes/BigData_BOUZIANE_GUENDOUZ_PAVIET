package fr.cytech.integration

import org.apache.spark.sql.SparkSession
import org.scalatest.funsuite.AnyFunSuite

class MainSpec extends AnyFunSuite {
  // Initialisation d'une session Spark pour les tests
  val spark: SparkSession = SparkSession.builder()
    .master("local[1]")
    .appName("Test Exercice 2")
    .getOrCreate()

  import spark.implicits._

  test("Validation du contrat : trip_distance doit être strictement positif") {
    // Création d'un petit échantillon de test
    val testData = Seq((1.5), (-0.5), (0.0)).toDF("trip_distance")

    // Application du filtre de validation
    val result = testData.filter($"trip_distance" > 0)

    // Vérification
    assert(result.count() == 1)
    assert(result.select("trip_distance").as[Double].first() == 1.5)
  }
}