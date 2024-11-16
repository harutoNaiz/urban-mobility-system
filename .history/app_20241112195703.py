from flask import Flask, request, render_template, redirect, url_for, session
import pymysql

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure you have a secret key for session management

# Database connection function
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='your_password',
        db='urban_mobility_db',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM Users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

    if user:
        session['user_id'] = user['user_id']  # Store user_id in session
        return redirect(url_for('dashboard'))
    else:
        return "Invalid credentials", 401

# Dashboard route (example)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    return render_template('dashboard.html', user_id=user_id)

# Route to display route options (this is just an example)
@app.route('/select_route', methods=['GET', 'POST'])
def select_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the user's selected route (example route_id)
    if request.method == 'POST':
        route_id = request.form['route_id']
        budget = request.form['budget']
        user_id = session['user_id']  # Get user_id from session
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Example of querying route options based on user budget
            cursor.execute("""
                SELECT * FROM Routes
                WHERE route_id = %s AND estimated_cost <= %s
            """, (route_id, budget))
            routes = cursor.fetchall()
        
        # Render the selected route and budget options
        return render_template('route_options.html', routes=routes, budget=budget)

    return render_template('select_route.html')

# Confirm booking route
@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    user_id = session.get('user_id')  # Fetch user_id from session
    
    if not user_id:
        return "Invalid or missing user_id", 400  # Return error if user_id is missing or invalid
    
    # Retrieve booking details from the form
    route_id = request.form['route_id']
    payment_amount = request.form['payment_amount']
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        # Check if the user is valid
        cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return "Invalid or missing user_id", 400  # Return error if user is not found
        
        # Proceed with the booking
        cursor.execute("INSERT INTO Bookings (user_id, route_id, amount) VALUES (%s, %s, %s)",
                       (user_id, route_id, payment_amount))
        connection.commit()
    
    return redirect(url_for('booking_confirmation'))

# Booking confirmation page
@app.route('/booking_confirmation')
def booking_confirmation():
    return "Booking confirmed successfully!"

# Error handling (for missing session or invalid user)
@app.errorhandler(404)
def not_found_error(error):
    return "Page not found!", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error!", 500

if __name__ == '__main__':
    app.run(debug=True)
