# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql
import json


app = Flask(__name__)

# Connect to the MySQL database
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route('/')
def index():
    return redirect(url_for('register_user'))

# Register a new user
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        preferred_transport = request.form['preferred_transport']
        commuting_pattern = request.form['commuting_pattern']
        
        # Create ContactInfo JSON
        contact_info = json.dumps({
            'Phone': phone,
            'Email': email
        })
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO Users (Name, ContactInfo, PreferredTransportMode, CommutingPattern) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, contact_info, preferred_transport, commuting_pattern))
            connection.commit()
        connection.close()
        
        return redirect(url_for('select_route'))
    
    return render_template('register.html')

# Route selection with congestion suggestion
@app.route('/select_route', methods=['GET', 'POST'])
def select_route():
    if request.method == 'POST':
        route_id = request.form['route_id']
        user_id = int(request.form['user_id'])

        # Check congestion level
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT CheckTrafficWarning(%s) AS traffic_warning", (route_id,))
            traffic_warning = cursor.fetchone()['traffic_warning']
        connection.close()
        
        return render_template('congestion_warning.html', traffic_warning=traffic_warning, route_id=route_id, user_id=user_id)
    
    # Fetch available routes
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Routes")
        routes = cursor.fetchall()
    connection.close()
    
    return render_template('select_route.html', routes=routes)

# Handle budget input and show options
@app.route('/suggest_routes', methods=['POST'])
def suggest_routes():
    budget = float(request.form['budget'])
    user_id = int(request.form['user_id'])
    route_id = int(request.form['route_id'])
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        sql = """
        SELECT Journeys.JourneyID, Journeys.TransportModeID, MIN(JourneyCost) AS Cost
        FROM Journeys
        WHERE StartLocation = (SELECT StartPoint FROM Routes WHERE RouteID = %s)
        AND EndLocation = (SELECT EndPoint FROM Routes WHERE RouteID = %s)
        AND JourneyCost <= %s
        GROUP BY Journeys.TransportModeID
        ORDER BY Cost
        """
        cursor.execute(sql, (route_id, route_id, budget))
        suggested_routes = cursor.fetchall()
    connection.close()
    
    return render_template('payment.html', suggested_routes=suggested_routes, user_id=user_id)

# Process booking and payment
@app.route('/process_booking', methods=['POST'])
def process_booking():
    user_id = int(request.form['user_id'])
    transport_mode_id = int(request.form['transport_mode_id'])
    journey_cost = float(request.form['cost'])
    payment_method = request.form['payment_method']
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        # Check capacity
        cursor.execute("SELECT Capacity, CurrentOccupancy FROM TransportModes WHERE TransportModeID = %s", (transport_mode_id,))
        transport_mode = cursor.fetchone()
        
        if transport_mode['CurrentOccupancy'] < transport_mode['Capacity']:
            # Proceed with booking
            cursor.execute("""
            INSERT INTO Journeys (UserID, StartLocation, EndLocation, StartTime, JourneyCost, TransportModeID)
            VALUES (%s, 'Unknown Start', 'Unknown End', NOW(), %s, %s)
            """, (user_id, journey_cost, transport_mode_id))
            connection.commit()
            
            # Update occupancy
            cursor.execute("UPDATE TransportModes SET CurrentOccupancy = CurrentOccupancy + 1 WHERE TransportModeID = %s", (transport_mode_id,))
            connection.commit()
            
            # Record payment
            cursor.execute("""
            INSERT INTO Payments (UserID, ProviderID, Amount, PaymentDate, PaymentMethod, DiscountApplied)
            VALUES (%s, (SELECT ProviderID FROM TransportModes WHERE TransportModeID = %s), %s, NOW(), %s, 0)
            """, (user_id, transport_mode_id, journey_cost, payment_method))
            connection.commit()
        else:
            return jsonify({'message': 'Capacity exceeded. Booking failed.'}), 400
    
    connection.close()
    return jsonify({'message': 'Booking and payment successful!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
