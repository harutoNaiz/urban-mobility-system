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

# Add these imports to your existing Flask imports
from functools import wraps

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Add these routes to your existing Flask application
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM AdminUsers WHERE Username = %s AND Password = %s", 
                         (username, password))
            admin = cursor.fetchone()
        connection.close()
        
        if admin:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid admin credentials", 401
            
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        # Fetch service providers
        cursor.execute("SELECT * FROM ServiceProviders")
        providers = cursor.fetchall()
        
        # Fetch transport modes
        cursor.execute("SELECT * FROM TransportModes")
        transport_modes = cursor.fetchall()
        
        # Fetch all payments
        cursor.execute("""
            SELECT p.*, u.Name as UserName 
            FROM Payments p 
            JOIN Users u ON p.UserID = u.UserID 
            ORDER BY PaymentDate DESC
        """)
        payments = cursor.fetchall()
    
    connection.close()
    return render_template('admin_dashboard.html', 
                         providers=providers, 
                         transport_modes=transport_modes,
                         payments=payments)

@app.route('/admin/add_provider', methods=['POST'])
@admin_required
def add_provider():
    if request.method == 'POST':
        name = request.form['name']
        contact_info = json.dumps({
            'email': request.form['email'],
            'phone': request.form['phone']
        })
        provider_type = request.form['type']
        fleet_size = request.form['fleet_size']
        service_area = json.dumps({
            'area': request.form['service_area']
        })
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ServiceProviders (Name, ContactInfo, Type, FleetSize, ServiceArea)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, contact_info, provider_type, fleet_size, service_area))
            connection.commit()
        connection.close()
        
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_transport', methods=['POST'])
@admin_required
def add_transport():
    if request.method == 'POST':
        mode_type = request.form['mode_type']
        provider_id = request.form['provider_id']
        capacity = request.form['capacity']
        schedule = json.dumps({
            'weekday': request.form['weekday_schedule'],
            'weekend': request.form['weekend_schedule']
        })
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO TransportModes (ModeType, ProviderID, Capacity, Schedule)
                VALUES (%s, %s, %s, %s)
            """, (mode_type, provider_id, capacity, schedule))
            connection.commit()
        connection.close()
        
        return redirect(url_for('admin_dashboard'))



@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('sign_in'))

# Inject payment history for user into the context
@app.context_processor
def inject_payments():
    user_id = session.get('user_id')
    payments = []
    if user_id:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # CRUDE OPERATION: Select recent payment history
            cursor.execute("""
                SELECT Amount, PaymentDate, PaymentMethod 
                FROM Payments 
                WHERE UserID = %s
                ORDER BY PaymentDate DESC 
                LIMIT 5
            """, (user_id,))
            payments = cursor.fetchall()
        connection.close()
    return {'payments': payments}

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
            # CRUDE OPERATION: Call stored procedure to fetch user by email and password
            cursor.callproc('sp_get_user_by_email_password', (email, password))
            user = cursor.fetchone()
        
        connection.close()

        if user:
            session['user_id'] = user['UserID']  # Session storage
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
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # CRUDE OPERATION: Insert new user via function
            cursor.execute("SELECT RegisterUser(%s, %s, %s, %s, %s) AS new_user_id",
                           (name, phone, email, password, preferred_transport))
            new_user_id = cursor.fetchone()['new_user_id']
            connection.commit()
        connection.close()
        
        session['user_id'] = new_user_id
        return redirect(url_for('sign_in'))

    return render_template('register.html')

# Route selection with congestion suggestion
@app.route('/select_route', methods=['GET', 'POST'])
def select_route():
    user_id = session.get('user_id')

    if request.method == 'POST':
        route_id = request.form['route_id']
        
        # CRUDE OPERATION: Check congestion level for route
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT CheckTrafficWarning(%s) AS traffic_warning", (route_id,))
            traffic_warning = cursor.fetchone()['traffic_warning']
        connection.close()

        if traffic_warning:
            return render_template('congestion_warning.html', traffic_warning=traffic_warning, route_id=route_id, user_id=user_id)
        else:
            return redirect(url_for('suggest_routes', route_id=route_id, user_id=user_id))
    
    # CRUDE OPERATION: Fetch available routes
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Routes")
        routes = cursor.fetchall()
    connection.close()
    
    return render_template('select_route.html', routes=routes, user_id=user_id)

# Handle budget input and show options
@app.route('/suggest_routes', methods=['POST'])
def suggest_routes():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'User not authenticated.'}), 401

    budget = float(request.form['budget'])
    route_id = int(request.form['route_id'])
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        # CRUDE OPERATION: Call stored procedure to suggest routes within budget
        cursor.callproc('sp_suggest_routes', (route_id, budget))
        suggested_routes = cursor.fetchall()
    connection.close()
    
    return render_template('payment.html', suggested_routes=suggested_routes, user_id=user_id)

# Process booking and payment
#triggers
@app.route('/process_booking', methods=['POST'])
def process_booking():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'User not authenticated.'}), 401

    transport_mode_id = int(request.form['transport_mode_id'])
    journey_cost = float(request.form['cost'])
    payment_method = request.form['payment_method']
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Check capacity and record journey
            cursor.execute("""
                INSERT INTO Journeys (StartTime, JourneyCost, TransportModeID, RouteID)
                VALUES (NOW(), %s, %s, (SELECT RouteID FROM Routes WHERE TransportModeID = %s))
            """, (journey_cost, transport_mode_id, transport_mode_id))
            connection.commit()
            
            # Record payment
            cursor.execute("""
                INSERT INTO Payments (UserID, ProviderID, Amount, PaymentMethod, DiscountApplied)
                VALUES (%s, (SELECT ProviderID FROM TransportModes WHERE TransportModeID = %s), %s, %s, 0)
            """, (user_id, transport_mode_id, journey_cost, payment_method))
            connection.commit()

    except pymysql.MySQLError as e:
        connection.rollback()
        return jsonify({'message': str(e)}), 400
    finally:
        connection.close()
    
    return jsonify({'message': 'Booking and payment successful!'}), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('sign_in'))

if __name__ == '__main__':
    app.run(debug=True)
