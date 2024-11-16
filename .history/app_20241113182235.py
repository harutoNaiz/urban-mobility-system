from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import pymysql
import json

# Import database config
# config.py
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'urban_mobility1',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for the session

# Connect to the MySQL database
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route('/')
def index():
    return redirect(url_for('sign_in'))

# Sign-in page for existing users
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM Users 
                WHERE JSON_UNQUOTE(JSON_EXTRACT(ContactInfo, '$.Email')) = %s 
                AND Password = %s
            """, (email, password))

            user = cursor.fetchone()
        connection.close()

        if user:
            # Store the user ID in the session
            session['user_id'] = user['UserID']
            # Redirect to route selection page
            return redirect(url_for('select_route'))
        else:
            return "User not found", 404

    return render_template('sign_in.html')

# Register a new user
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        preferred_transport = request.form['preferred_transport']
        
        # Create ContactInfo JSON
        contact_info = json.dumps({
            'Phone': phone,
            'Email': email
        })
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO Users (Name, ContactInfo, PreferredTransportMode, Password) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, contact_info, preferred_transport, password))
            new_user_id = cursor.lastrowid
            connection.commit()
        connection.close()
        
        # Store the new user ID in the session
        session['user_id'] = new_user_id
        
        # Redirect to the route selection page
        return redirect(url_for('sign_in'))

    return render_template('register.html')

# Route selection with congestion suggestion
@app.route('/select_route', methods=['GET', 'POST'])
def select_route():
    # Get the user ID from the session
    user_id = session.get('user_id')

    if request.method == 'POST':
        route_id = request.form['route_id']

        # Check congestion level for the selected route
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT CheckTrafficWarning(%s) AS traffic_warning", (route_id,))
            traffic_warning = cursor.fetchone()['traffic_warning']
        connection.close()

        if traffic_warning:##########################
            return render_template('congestion_warning.html', traffic_warning=traffic_warning, route_id=route_id, user_id=user_id)
        else:
            return redirect(url_for('suggest_routes', route_id=route_id, user_id=user_id))
    
    # Fetch available routes for user
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Routes")
        routes = cursor.fetchall()
    connection.close()
    
    return render_template('select_route.html', routes=routes, user_id=user_id)

# Handle budget input and show options
@app.route('/suggest_routes', methods=['POST'])
def suggest_routes():
    # Get the user ID from the session
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'message': 'User not authenticated.'}), 401

    budget = float(request.form['budget'])
    route_id = int(request.form['route_id'])
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        sql = """
        SELECT Journeys.JourneyID, Journeys.TransportModeID, MIN(JourneyCost) AS Cost
        FROM Journeys
        WHERE RouteID = %s
        AND JourneyCost <= %s
        GROUP BY Journeys.JourneyID, Journeys.TransportModeID
        ORDER BY Cost
        """
        
        cursor.execute(sql, (route_id, budget))  # Use %s placeholders for parameters
        suggested_routes = cursor.fetchall()
    connection.close()
    
    return render_template('payment.html', suggested_routes=suggested_routes, user_id=user_id)



@app.route('/process_booking', methods=['POST'])
def process_booking():
    # Get the user ID from the session
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'message': 'User not authenticated.'}), 401

    transport_mode_id = int(request.form['transport_mode_id'])
    journey_cost = float(request.form['cost'])
    payment_method = request.form['payment_method']
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        # Check capacity
        cursor.execute("SELECT Capacity, CurrentOccupancy FROM TransportModes WHERE TransportModeID = %s", (transport_mode_id,))
        transport_mode = cursor.fetchone()
        
        if transport_mode['CurrentOccupancy'] < transport_mode['Capacity']:
            # Get RouteID based on TransportModeID and ensure JourneyCost fits within budget
            cursor.execute("""
            SELECT RouteID FROM Routes
            WHERE TransportModeID = %s
            """, (transport_mode_id,))
            route = cursor.fetchone()

            if route:
                route_id = route['RouteID']
                
                # Proceed with booking
                cursor.execute("""
                INSERT INTO Journeys (RouteID, StartTime, JourneyCost, TransportModeID, UserID)
                VALUES (%s, NOW(), %s, %s, %s)
                """, (route_id, journey_cost, transport_mode_id, user_id))
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
                return jsonify({'message': 'Route not found.'}), 404
        else:
            return jsonify({'message': 'Capacity exceeded. Booking failed.'}), 400
    
    connection.close()
    return jsonify({'message': 'Booking and payment successful!'}), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect(url_for('sign_in'))  # Redirect to sign-in page


if __name__ == '__main__':
    app.run(debug=True)