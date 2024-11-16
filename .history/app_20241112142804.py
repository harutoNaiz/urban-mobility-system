from flask import Flask, render_template, request, jsonify, redirect, url_for
import pymysql

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'urban_mobility1',
    'cursorclass': pymysql.cursors.DictCursor
}

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        contact_info = request.form['contact_info']
        preferred_mode = request.form['preferred_mode']
        
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute('''INSERT INTO Users (Name, ContactInfo, PreferredTransportMode) 
                              VALUES (%s, %s, %s)''', (name, contact_info, preferred_mode))
            connection.commit()
        connection.close()
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
        
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT RouteID FROM Routes WHERE StartPoint = %s AND EndPoint = %s", 
                           (start_location, end_location))
            route = cursor.fetchone()
            
            if route:
                route_id = route['RouteID']
                cursor.execute("SELECT CheckTrafficWarning(%s) AS TrafficWarning", (route_id,))
                warning = cursor.fetchone()['TrafficWarning']
                
                cursor.execute("CALL SuggestLowestCostRoute(%s, %s, %s)", (start_location, end_location, user_id))
                route_option = cursor.fetchone()
                suggested_route = route_option if route_option and route_option['LowestCost'] <= budget else None
                
                return render_template('route_options.html', warning=warning, suggested_route=suggested_route)
        connection.close()
    return render_template('journey.html')

# Book Journey
@app.route('/book', methods=['POST'])
def book():
    transport_mode_id = request.form['transport_mode_id']
    user_id = request.form['user_id']
    start_location = request.form['start_location']
    end_location = request.form['end_location']
    journey_cost = float(request.form['journey_cost'])
    
    connection = pymysql.connect(**db_config)
    with connection.cursor() as cursor:
        cursor.callproc('CheckCapacityAndBook', [transport_mode_id, user_id, start_location, end_location, journey_cost])
        connection.commit()
        
        provider_id = request.form['provider_id']
        payment_method = request.form['payment_method']
        discount_applied = True if request.form.get('discount_applied') == 'on' else False
        
        cursor.execute('''INSERT INTO Payments (UserID, ProviderID, Amount, PaymentDate, PaymentMethod, DiscountApplied) 
                          VALUES (%s, %s, %s, NOW(), %s, %s)''', (user_id, provider_id, journey_cost, payment_method, discount_applied))
        connection.commit()
    connection.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
