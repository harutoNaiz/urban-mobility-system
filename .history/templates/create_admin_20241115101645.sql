-- First create admin user and grant privileges
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin_password';

-- Grant specific privileges to admin user
GRANT SELECT, INSERT, UPDATE, DELETE ON urban_mobility1.ServiceProviders TO 'admin'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON urban_mobility1.TransportModes TO 'admin'@'localhost';
GRANT SELECT ON urban_mobility1.Payments TO 'admin'@'localhost';

-- Create Admin credentials table
CREATE TABLE AdminUsers (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin user
INSERT INTO AdminUsers (Username, Password) VALUES ('admin', 'admin123');