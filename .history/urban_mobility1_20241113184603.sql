-- Users table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    ContactInfo JSON,  -- Using JSON to store structured contact info
    PreferredTransportMode VARCHAR(50),
    Password VARCHAR(255)
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
-- Step 1: Add Service Providers
INSERT INTO ServiceProviders (Name, ContactInfo, Type, FleetSize, ServiceArea) VALUES
('Bangalore Metropolitan Transport Corporation', '{"Phone": "08012345678", "Email": "contact@bmrtc.com"}', 'Public', 500, '{"City": "Bangalore"}'),
('Bangalore Metro Rail Corporation Limited', '{"Phone": "08087654321", "Email": "contact@bmrc.com"}', 'Public', 100, '{"City": "Bangalore"}'),
('Uber Bangalore', '{"Phone": "08098765432", "Email": "support@uber.com"}', 'Private', 300, '{"City": "Bangalore"}'),
('Bounce Bikes', '{"Phone": "08045678901", "Email": "contact@bounce.com"}', 'Private', 200, '{"City": "Bangalore"}');

-- Step 2: Add Transport Modes (linked to ServiceProviders)
INSERT INTO TransportModes (ModeType, ProviderID, Capacity, Schedule) VALUES
('Bus', 5, 50, '{"Weekdays": "5:00 AM - 11:00 PM", "Weekends": "6:00 AM - 10:00 PM"}'),
('Metro', 6, 300, '{"Weekdays": "6:00 AM - 11:00 PM", "Weekends": "6:00 AM - 11:00 PM"}'),
('Ride-Share', 7, 4, '{"Available 24/7": true}'),
('Bike-Share', 8, 1, '{"Available 24/7": true}');

-- Step 3: Add Routes (linked to TransportModes)
INSERT INTO Routes (TransportModeID, StartPoint, EndPoint, RouteMap, Distance, EstimatedTime, MaxTrafficLevel, CurrentTrafficLevel) VALUES
(17, 'Majestic', 'Whitefield', '{"Path": ["Majestic", "MG Road", "Ulsoor", "Whitefield"]}', 20.5, '01:15:00', 'Medium', 'Low'),
(18, 'Nagasandra', 'Yelachenahalli', '{"Path": ["Nagasandra", "Rajajinagar", "MG Road", "Yelachenahalli"]}', 18.0, '00:45:00', 'Low', 'Low'),
(19, 'Koramangala', 'Electronic City', '{"Path": ["Koramangala", "Silk Board", "HSR Layout", "Electronic City"]}', 12.0, '00:30:00', 'High', 'Medium'),
(20, 'Indiranagar', 'Kormangala', '{"Path": ["Indiranagar", "Domlur", "Ejipura", "Koramangala"]}', 5.0, '00:20:00', 'Low', 'Low');

