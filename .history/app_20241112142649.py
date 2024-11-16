from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_mysqldb import MySQL
import pymysql.cursors  # Use PyMySQL instead of MySQLdb

app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'urban_mobility1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Ensures cursors return dictionaries

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        contact_info = request.form['contact_info']
        preferred_mode = request.form['preferred_mode']
        
        cursor = mysql.connection.cursor()
        cursor.execute('''INSERT INTO Users (Name, ContactInfo, PreferredTransportMode) 
                          VALUES (%s, %s, %s)''', (name, contact_info, preferred_mode))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('journey_planner'))
    return render_template('register.html')

# Journey Planner
@app.route('/journey', methods=['GET', 'POST'])
def journey_planner():
    if request.method == 'POST':
        start_location = request.form['start_location']
        end_location = request.form['end_location']
        user_id = request.form['user_id']
        budget = float(request.form['budget'])
        
        cursor = mysql.connection.cursor()
        
        # Check for traffic warning
        cursor.execute("SELECT RouteID FROM Routes WHERE StartPoint = %s AND EndPoint = %s", 
                       (start_location, end_location))
        route = cursor.fetchone()
        
        if route:
            route_id = route['RouteID']
            cursor.execute("SELECT CheckTrafficWarning(%s) AS TrafficWarning", (route_id,))
            warning = cursor.fetchone()['TrafficWarning']
            
            # Suggest cheapest available route within budget
            cursor.execute("CALL SuggestLowestCostRoute(%s, %s, %s)", (start_location, end_location, user_id))
            route_option = cursor.fetchone()
            if route_option and route_option['LowestCost'] <= budget:
                suggested_route = route_option
            else:
                suggested_route = None
            
            return render_template('route_options.html', warning=warning, suggested_route=suggested_route)
    return render_template('journey.html')

# Book Journey
@app.route('/book', methods=['POST'])
def book():
    transport_mode_id = request.form['transport_mode_id']
    user_id = request.form['user_id']
    start_location = request.form['start_location']
    end_location = request.form['end_location']
    journey_cost = float(request.form['journey_cost'])
    
    cursor = mysql.connection.cursor()
    cursor.callproc('CheckCapacityAndBook', [transport_mode_id, user_id, start_location, end_location, journey_cost])
    mysql.connection.commit()
    
    # Payment process
    provider_id = request.form['provider_id']
    payment_method = request.form['payment_method']
    discount_applied = True if request.form.get('discount_applied') == 'on' else False
    
    cursor.execute('''INSERT INTO Payments (UserID, ProviderID, Amount, PaymentDate, PaymentMethod, DiscountApplied) 
                      VALUES (%s, %s, %s, NOW(), %s, %s)''', (user_id, provider_id, journey_cost, payment_method, discount_applied))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
