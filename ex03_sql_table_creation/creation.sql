DROP TABLE IF EXISTS Fact_Taxi_Trips CASCADE;
DROP TABLE IF EXISTS Taxi_Zone CASCADE;
DROP TABLE IF EXISTS Borough CASCADE;
DROP TABLE IF EXISTS Vendor CASCADE;
DROP TABLE IF EXISTS Payment_Type CASCADE;
DROP TABLE IF EXISTS Rate_Code CASCADE;
-- Table pour les arrondissements
CREATE TABLE Borough (
                         borough_id SERIAL PRIMARY KEY,
                         name VARCHAR(50) NOT NULL
);

-- Table pour les fournisseurs
CREATE TABLE Vendor (
                        vendor_id INT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL
);

-- Table pour les types de paiement
CREATE TABLE Payment_Type (
                              payment_type_id INT PRIMARY KEY,
                              description VARCHAR(50) NOT NULL
);

-- Table pour les codes tarifaires
CREATE TABLE Rate_Code (
                           rate_code_id INT PRIMARY KEY,
                           description VARCHAR(50) NOT NULL
);

-- Table pour les zones de taxi qui référence un arrondissement
CREATE TABLE Taxi_Zone (
                           zone_id INT PRIMARY KEY,
                           name VARCHAR(255),
                           borough_id INT,
                           CONSTRAINT fk_borough
                               FOREIGN KEY (borough_id)
                                   REFERENCES Borough(borough_id)
);
CREATE TABLE Fact_Taxi_Trips (
                                 trip_id SERIAL PRIMARY KEY,
                                 vendor_id INT REFERENCES Vendor(vendor_id),
                                 pickup_datetime TIMESTAMP NOT NULL,
                                 dropoff_datetime TIMESTAMP NOT NULL,
                                 passenger_count INT,
                                 trip_distance NUMERIC(10,2),
                                 rate_code_id INT REFERENCES Rate_Code(rate_code_id),
                                 pu_location_id INT REFERENCES Taxi_Zone(zone_id),
                                 do_location_id INT REFERENCES Taxi_Zone(zone_id),
                                 payment_type_id INT REFERENCES Payment_Type(payment_type_id),


                                 fare_amount NUMERIC(10,2),
                                 extra NUMERIC(10,2),
                                 mta_tax NUMERIC(10,2),
                                 tip_amount NUMERIC(10,2),
                                 tolls_amount NUMERIC(10,2),
                                 improvement_surcharge NUMERIC(10,2),
                                 total_amount NUMERIC(10,2) NOT NULL,
                                 congestion_surcharge NUMERIC(10,2)
);