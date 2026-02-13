name := "ex02_data_ingestion"

version := "0.1"

// Utilisation d'une version compatible avec Spark 3.x
scalaVersion := "2.13.17"

val sparkVersion = "3.5.0"
val hadoopVersion = "3.3.4"

libraryDependencies ++= Seq(
  // Spark Core et SQL
  "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-sql"  % sparkVersion % "provided",

  // Connecteurs pour Minio (S3A)
  "org.apache.hadoop" % "hadoop-aws" % hadoopVersion,
  "com.amazonaws"     % "aws-java-sdk-bundle" % "1.12.262",

  // Pour les tests unitaires
  "org.scalatest" %% "scalatest" % "3.2.15" % Test
)
libraryDependencies += "org.postgresql" % "postgresql" % "42.6.0"

assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
}