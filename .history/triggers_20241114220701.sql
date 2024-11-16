

CREATE TRIGGER check_transport_capacity
BEFORE INSERT ON Journeys
FOR EACH ROW
BEGIN
    DECLARE current_occupancy INT;
    DECLARE max_capacity INT;
    
    SELECT CurrentOccupancy, Capacity INTO current_occupancy, max_capacity
    FROM TransportModes
    WHERE TransportModeID = NEW.TransportModeID;
    
    IF current_occupancy >= max_capacity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Capacity exceeded for this transport mode.';
    ELSE
        UPDATE TransportModes
        SET CurrentOccupancy = CurrentOccupancy + 1
        WHERE TransportModeID = NEW.TransportModeID;
    END IF;
END  ;


CREATE TRIGGER update_route_traffic
AFTER INSERT ON TrafficConditions
FOR EACH ROW
BEGIN
    DECLARE avg_congestion_level ENUM('Low', 'Medium', 'High');
    
    SELECT CASE
               WHEN AVG(CongestionLevel) > 2 THEN 'High'
               WHEN AVG(CongestionLevel) > 1 THEN 'Medium'
               ELSE 'Low'
           END INTO avg_congestion_level
    FROM TrafficConditions
    WHERE RouteID = NEW.RouteID;
    
    UPDATE Routes
    SET CurrentTrafficLevel = avg_congestion_level
    WHERE RouteID = NEW.RouteID;
END  ;


CREATE TRIGGER set_payment_date
BEFORE INSERT ON Payments
FOR EACH ROW
BEGIN
    IF NEW.PaymentDate IS NULL THEN
        SET NEW.PaymentDate = NOW();
    END IF;
END  ;
