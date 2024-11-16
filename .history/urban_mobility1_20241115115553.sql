-- Users table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    ContactInfo JSON,  -- Using JSON to store structured contact info
    PreferredTransportMode VARCHAR(50),
    Password VARCHAR(255)
);

CREATE TABLE AdminUsers (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Journeys table
CREATE TABLE Journeys (
    JourneyID INT AUTO_INCREMENT PRIMARY KEY,
    StartTime DATETIME,
    EndTime DATETIME,
    JourneyCost DECIMAL(10, 2),
    TransportModeID INT,
    RouteID INT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (TransportModeID) REFERENCES TransportModes(TransportModeID),
    ADD CONSTRAINT fk_route FOREIGN KEY (RouteID) REFERENCES Routes(RouteID);
);

-- Transport Modes table with capacity limits
CREATE TABLE TransportModes (
    TransportModeID INT AUTO_INCREMENT PRIMARY KEY,
    ModeType VARCHAR(50) NOT NULL,  -- E.g., Bus, Subway, Bike, Ride-Share, Pedestrian
    ProviderID INT,
    Capacity INT,  -- Maximum capacity of the vehicle
    CurrentOccupancy INT DEFAULT 0,  -- Tracks current number of passengers
    Schedule JSON,
    FOREIGN KEY (ProviderID) REFERENCES ServiceProviders(ProviderID)
);

-- Routes table with traffic information
CREATE TABLE Routes (
    RouteID INT AUTO_INCREMENT PRIMARY KEY,
    TransportModeID INT,
    StartPoint VARCHAR(100),
    EndPoint VARCHAR(100),
    RouteMap JSON,
    Distance DECIMAL(10, 2),
    EstimatedTime TIME,
    MaxTrafficLevel ENUM('Low', 'Medium', 'High') DEFAULT 'Low',
    CurrentTrafficLevel ENUM('Low', 'Medium', 'High') DEFAULT 'Low',
    FOREIGN KEY (TransportModeID) REFERENCES TransportModes(TransportModeID)
);

-- Service Providers table
CREATE TABLE ServiceProviders (
    ProviderID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    ContactInfo JSON,
    Type ENUM('Public', 'Private') DEFAULT 'Public',
    FleetSize INT,
    ServiceArea JSON
);

-- TrafficConditions table to store real-time updates
CREATE TABLE TrafficConditions (
    TrafficID INT AUTO_INCREMENT PRIMARY KEY,
    RouteID INT,
    CongestionLevel ENUM('Low', 'Medium', 'High'),
    IncidentReports TEXT,
    WeatherImpact VARCHAR(50),
    RealTimeUpdates DATETIME,
    FOREIGN KEY (RouteID) REFERENCES Routes(RouteID)
);

-- Payments table
CREATE TABLE Payments (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    ProviderID INT,
    Amount DECIMAL(10, 2),
    PaymentDate DATETIME,
    PaymentMethod ENUM('Card', 'Cash', 'Online') DEFAULT 'Online',
    DiscountApplied BOOLEAN,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (ProviderID) REFERENCES ServiceProviders(ProviderID)
);