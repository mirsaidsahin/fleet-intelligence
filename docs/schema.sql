-- Fleet Intelligence database schema for a new, empty database.
-- This file only creates missing objects. It does not drop or modify existing data.
-- Select the target database first (for example: USE omnilogistics;).

CREATE TABLE IF NOT EXISTS brands (
  BrandID int NOT NULL AUTO_INCREMENT,
  BrandName varchar(50) NOT NULL,
  Country varchar(50) DEFAULT NULL,
  PRIMARY KEY (BrandID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS customers (
  CustomerID int NOT NULL AUTO_INCREMENT,
  CompanyName varchar(100) NOT NULL,
  ContactPerson varchar(50) DEFAULT NULL,
  Phone varchar(20) DEFAULT NULL,
  Address varchar(255) DEFAULT NULL,
  PRIMARY KEY (CustomerID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS garages (
  GarageID int NOT NULL AUTO_INCREMENT,
  City varchar(100) NOT NULL,
  Capacity int NOT NULL,
  PRIMARY KEY (GarageID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS drivers (
  DriverID int NOT NULL AUTO_INCREMENT,
  FirstName varchar(50) NOT NULL,
  LastName varchar(50) NOT NULL,
  LicenseType varchar(5) NOT NULL,
  ExperienceYears int NOT NULL,
  Phone varchar(20) DEFAULT NULL,
  MentorID int DEFAULT NULL,
  PRIMARY KEY (DriverID),
  KEY fk_driver_mentor (MentorID),
  CONSTRAINT fk_driver_mentor FOREIGN KEY (MentorID) REFERENCES drivers (DriverID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS routes (
  RouteID int NOT NULL AUTO_INCREMENT,
  DepartureCity varchar(100) NOT NULL,
  ArrivalCity varchar(100) NOT NULL,
  DistanceKm int NOT NULL,
  EstimatedHours decimal(4,1) NOT NULL,
  SpecialistDriverID int DEFAULT NULL,
  PRIMARY KEY (RouteID),
  KEY fk_route_specialist (SpecialistDriverID),
  CONSTRAINT fk_route_specialist FOREIGN KEY (SpecialistDriverID) REFERENCES drivers (DriverID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cargos (
  CargoID int NOT NULL AUTO_INCREMENT,
  CargoName varchar(100) NOT NULL,
  WeightKg int NOT NULL,
  ValueEUR decimal(10,2) NOT NULL,
  DefaultRouteID int DEFAULT NULL,
  PRIMARY KEY (CargoID),
  KEY fk_cargo_route (DefaultRouteID),
  CONSTRAINT fk_cargo_route FOREIGN KEY (DefaultRouteID) REFERENCES routes (RouteID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS trucks (
  TruckID int NOT NULL AUTO_INCREMENT,
  BrandID int DEFAULT NULL,
  Model varchar(50) NOT NULL,
  ProductionYear int DEFAULT NULL,
  RequiredLicense varchar(5) NOT NULL,
  PlateNumber varchar(20) NOT NULL,
  Mileage int DEFAULT 0,
  GarageID int DEFAULT NULL,
  AssignedDriverID int DEFAULT NULL,
  PRIMARY KEY (TruckID),
  UNIQUE KEY PlateNumber (PlateNumber),
  UNIQUE KEY AssignedDriverID (AssignedDriverID),
  KEY BrandID (BrandID),
  KEY fk_truck_garage (GarageID),
  CONSTRAINT fk_truck_driver FOREIGN KEY (AssignedDriverID) REFERENCES drivers (DriverID),
  CONSTRAINT fk_truck_garage FOREIGN KEY (GarageID) REFERENCES garages (GarageID),
  CONSTRAINT fk_truck_brand FOREIGN KEY (BrandID) REFERENCES brands (BrandID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jobs (
  JobID int NOT NULL AUTO_INCREMENT,
  TruckID int NOT NULL,
  DriverID int NOT NULL,
  CargoID int NOT NULL,
  RouteID int NOT NULL,
  StartDate datetime DEFAULT NULL,
  Status enum('Pending','In Transit','Completed','Cancelled') DEFAULT 'Pending',
  EndDate datetime DEFAULT NULL,
  CustomerID int DEFAULT NULL,
  RevenueEUR decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (JobID),
  KEY TruckID (TruckID),
  KEY DriverID (DriverID),
  KEY CargoID (CargoID),
  KEY RouteID (RouteID),
  KEY fk_job_customer (CustomerID),
  CONSTRAINT fk_job_customer FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID),
  CONSTRAINT fk_job_truck FOREIGN KEY (TruckID) REFERENCES trucks (TruckID),
  CONSTRAINT fk_job_driver FOREIGN KEY (DriverID) REFERENCES drivers (DriverID),
  CONSTRAINT fk_job_cargo FOREIGN KEY (CargoID) REFERENCES cargos (CargoID),
  CONSTRAINT fk_job_route FOREIGN KEY (RouteID) REFERENCES routes (RouteID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE OR REPLACE VIEW vw_activejobsreport AS
SELECT j.JobID,
       CONCAT(d.FirstName, ' ', d.LastName) AS DriverName,
       t.PlateNumber,
       c.CargoName,
       r.DepartureCity,
       r.ArrivalCity,
       j.Status
FROM jobs AS j
JOIN drivers AS d ON j.DriverID = d.DriverID
JOIN trucks AS t ON j.TruckID = t.TruckID
JOIN cargos AS c ON j.CargoID = c.CargoID
JOIN routes AS r ON j.RouteID = r.RouteID;
