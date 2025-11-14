
# app.py - Flask Backend Logic

from flask import Flask, request, redirect, url_for, render_template, session, g
import sqlite3
import hashlib 

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_CHANGE_ME' # IMPORTANT: Change this!
DATABASE = 'sokoswift.db' # SQLite database file

# --- Database Helper Functions ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Security Helper ---

def hash_password(password):
    # In a real app, use bcrypt, but for demonstration, we use SHA256:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, password):
    return hashed_password == hash_password(password)

# --- Helper Function (Placeholder for Cart Data) ---

def get_cart(session):
    # This is a sample cart. In a real app, this would be dynamic from the session/database.
    return [
        {'product_id': 1, 'quantity': 2, 'unit_price': 2499.00},  # Pro Wireless Earbuds
        {'product_id': 3, 'quantity': 1, 'unit_price': 3200.00}   # Portable Bluetooth Speaker
    ]

# --- Routes ---

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # MODIFIED: Added links to the order features
    return f"""
        <h1>Welcome back, Customer ID: {session['user_id']}!</h1>
        <h2>SokoSwift Dashboard</h2>
        <p>You are logged in.</p>
        <p><a href="{url_for('checkout')}">Go to Simulated Checkout</a></p>
        <p><a href="{url_for('view_orders')}">View My Orders</a></p>
        <p><a href="{url_for('logout')}">Log Out</a></p>
    """


@app.route('/register', methods=['GET', 'POST'])
def register():
    # ... (Registration logic from earlier steps) ...
    if request.method == 'POST':
        db = get_db()
        try:
            name_parts = request.form['name'].split()
            first_name = name_parts[0]
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            db.execute(
                "INSERT INTO Customers (first_name, last_name, email, password_hash, phone_number) VALUES (?, ?, ?, ?, ?)",
                (first_name, last_name, request.form['email'], 
                 hash_password(request.form['password']), 
                 request.form['phone'])
            )
            db.commit()
            return redirect(url_for('login', success='Registration Successful!'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Email or Phone already registered.')
        except Exception as e:
            return render_template('register.html', error=f'An error occurred: {e}')
    return render_template('register.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Login logic from earlier steps) ...
    if request.method == 'POST':
        db = get_db()
        cursor = db.execute("SELECT * FROM Customers WHERE email = ?", (request.form['email'],))
        user = cursor.fetchone()

        if user and check_password(user['password_hash'], request.form['password']):
            session['logged_in'] = True
            session['user_id'] = user['customer_id']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid email or password.')
    
    success_message = request.args.get('success')
    return render_template('login.html', success=success_message) 

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/checkout')
def checkout():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('checkout.html')

@app.route('/checkout/submit', methods=['POST'])
def submit_order():
    # ... (Order submission logic from earlier steps) ...
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    customer_id = session['user_id']
    delivery_address = request.form.get('delivery_address')
    payment_method = request.form.get('payment_method')
    
    cart_items = get_cart(session)
    if not cart_items:
        return "Your cart is empty!", 400

    total_amount = sum(item['quantity'] * item['unit_price'] for item in cart_items)
    
    db = get_db()
    
    try:
        # 2. Insert into the Orders table (High-Level Record)
        cursor = db.execute(
            "INSERT INTO Orders (customer_id, total_amount, payment_method, delivery_address, order_status) VALUES (?, ?, ?, ?, ?)",
            (customer_id, total_amount, payment_method, delivery_address, 'Processing')
        )
        
        order_id = cursor.lastrowid 
        
        # 3. Insert into the Order_Items table (Line Items)
        for item in cart_items:
            db.execute(
                "INSERT INTO Order_Items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, item['product_id'], item['quantity'], item['unit_price'])
            )
            
        db.commit()
        
        return f"Order {order_id} successfully placed! Total: KSh {total_amount:.2f}. Delivery to: {delivery_address}. <a href='{url_for('view_orders')}'>View Orders</a>"

    except Exception as e:
        db.rollback()
        return f"Error placing order: {e}", 500


@app.route('/orders')
def view_orders():
    # ... (Order retrieval logic from earlier steps) ...
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    customer_id = session['user_id']
    db = get_db()
    
    orders_cursor = db.execute(
        "SELECT order_id, order_date, total_amount, order_status FROM Orders WHERE customer_id = ? ORDER BY order_date DESC",
        (customer_id,)
    )
    orders = orders_cursor.fetchall()
    
    order_details = {}
    for order in orders:
        items_cursor = db.execute(
            "SELECT product_id, quantity, unit_price FROM Order_Items WHERE order_id = ?",
            (order['order_id'],)
        )
        order_details[order['order_id']] = items_cursor.fetchall()
    
    return render_template('orders.html', orders=orders, order_details=order_details)


if __name__ == '__main__':
    # REMEMBER: Uncomment init_db() ONLY ONCE to create the database, then comment it out again.
    # init_db() 
    app.run(debug=True)