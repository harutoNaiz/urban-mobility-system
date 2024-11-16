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
    
# Add this new route to your Flask application
@app.route('/admin/delete_provider/<int:provider_id>', methods=['POST'])
@admin_required
def delete_provider(provider_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # First check if there are any transport modes associated with this provider
            cursor.execute("SELECT COUNT(*) as count FROM TransportModes WHERE ProviderID = %s", (provider_id,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                return jsonify({
                    'success': False, 
                    'message': 'Cannot delete provider with associated transport modes'
                }), 400
            
            # Fixed SQL query - removed incorrect quotes around table and column names
            cursor.execute("DELETE FROM ServiceProviders WHERE ProviderID = %s", (provider_id,))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Provider deleted successfully'
            })
            
    except Exception as e:
        connection.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        connection.close()

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

from flask import jsonify
from datetime import datetime, time
import json

# Add these routes to your existing Flask application

@app.route('/admin/traffic/update/<int:route_id>', methods=['POST'])
@admin_required
def update_traffic(route_id):
    """Update traffic levels for a specific route"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # First get current occupancy data
            cursor.execute("""
                SELECT tm.CurrentOccupancy, tm.Capacity, r.CurrentTrafficLevel
                FROM Routes r
                JOIN TransportModes tm ON r.TransportModeID = tm.TransportModeID
                WHERE r.RouteID = %s
            """, (route_id,))
            route_data = cursor.fetchone()
            
            if not route_data:
                return jsonify({
                    'success': False,
                    'message': 'Route not found'
                }), 404
            
            # Calculate occupancy ratio
            occupancy_ratio = (route_data['CurrentOccupancy'] / route_data['Capacity']) * 100
            
            # Determine new traffic level
            new_traffic_level = determine_traffic_level(
                occupancy_ratio=occupancy_ratio,
                current_time=datetime.now().time(),
                route_id=route_id,
                cursor=cursor
            )
            
            # Update route traffic level
            cursor.execute("""
                UPDATE Routes 
                SET CurrentTrafficLevel = %s
                WHERE RouteID = %s
            """, (new_traffic_level, route_id))
            
            # Log traffic condition
            cursor.execute("""
                INSERT INTO TrafficConditions 
                (RouteID, CongestionLevel, RealTimeUpdates)
                VALUES (%s, %s, NOW())
            """, (route_id, new_traffic_level))
            
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': f'Traffic updated to {new_traffic_level}',
                'new_traffic_level': new_traffic_level,
                'occupancy_ratio': occupancy_ratio
            })
            
    except Exception as e:
        connection.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        connection.close()

@app.route('/admin/traffic/monitor', methods=['GET'])
@admin_required
def monitor_traffic():
    """Get traffic monitoring dashboard data"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get all active routes with their current traffic status
            cursor.execute("""
                SELECT 
                    r.RouteID,
                    r.StartPoint,
                    r.EndPoint,
                    r.CurrentTrafficLevel,
                    tm.CurrentOccupancy,
                    tm.Capacity,
                    sp.Name as ProviderName,
                    tc.IncidentReports,
                    tc.WeatherImpact,
                    tc.RealTimeUpdates
                FROM Routes r
                JOIN TransportModes tm ON r.TransportModeID = tm.TransportModeID
                JOIN ServiceProviders sp ON tm.ProviderID = sp.ProviderID
                LEFT JOIN (
                    SELECT 
                        RouteID,
                        IncidentReports,
                        WeatherImpact,
                        RealTimeUpdates,
                        ROW_NUMBER() OVER (PARTITION BY RouteID ORDER BY RealTimeUpdates DESC) as rn
                    FROM TrafficConditions
                ) tc ON tc.RouteID = r.RouteID AND tc.rn = 1
            """)
            routes = cursor.fetchall()
            
            # Calculate statistics
            traffic_stats = {
                'high_traffic_routes': len([r for r in routes if r['CurrentTrafficLevel'] == 'High']),
                'medium_traffic_routes': len([r for r in routes if r['CurrentTrafficLevel'] == 'Medium']),
                'low_traffic_routes': len([r for r in routes if r['CurrentTrafficLevel'] == 'Low']),
                'total_routes': len(routes)
            }
            
            return jsonify({
                'success': True,
                'routes': routes,
                'statistics': traffic_stats
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        connection.close()

def determine_traffic_level(occupancy_ratio, current_time, route_id, cursor):
    """
    Determine traffic level based on multiple factors:
    - Current occupancy
    - Time of day
    - Historical patterns
    - Weather impact (if available)
    """
    # Base traffic level from occupancy
    if occupancy_ratio >= 80:
        base_level = 'High'
    elif occupancy_ratio >= 50:
        base_level = 'Medium'
    else:
        base_level = 'Low'
    
    # Time-based adjustments (peak hours)
    peak_morning_start = time(7, 0)  # 7:00 AM
    peak_morning_end = time(9, 0)    # 9:00 AM
    peak_evening_start = time(16, 0) # 4:00 PM
    peak_evening_end = time(18, 0)   # 6:00 PM
    
    is_peak_time = (
        (peak_morning_start <= current_time <= peak_morning_end) or
        (peak_evening_start <= current_time <= peak_evening_end)
    )
    
    # Check weather impact
    cursor.execute("""
        SELECT WeatherImpact 
        FROM TrafficConditions 
        WHERE RouteID = %s 
        ORDER BY RealTimeUpdates DESC 
        LIMIT 1
    """, (route_id,))
    weather_data = cursor.fetchone()
    
    has_weather_impact = (
        weather_data and 
        weather_data['WeatherImpact'] and 
        weather_data['WeatherImpact'].lower() not in ['clear', 'none', '']
    )
    
    # Adjust traffic level based on factors
    if is_peak_time and base_level != 'High':
        # Increase traffic level during peak hours
        if base_level == 'Low':
            return 'Medium'
        elif base_level == 'Medium':
            return 'High'
    
    if has_weather_impact and base_level != 'High':
        # Increase traffic level due to weather
        if base_level == 'Low':
            return 'Medium'
        elif base_level == 'Medium':
            return 'High'
    
    return base_level

# Optional: Add WebSocket support for real-time updates
try:
    from flask_socketio import SocketIO, emit
    
    socketio = SocketIO(app)
    
    def broadcast_traffic_update(route_id, new_level):
        """Broadcast traffic updates to connected clients"""
        socketio.emit('traffic_update', {
            'route_id': route_id,
            'traffic_level': new_level,
            'timestamp': datetime.now().isoformat()
        })
except ImportError:
    # SocketIO not available
    def broadcast_traffic_update(route_id, new_level):
        pass

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
