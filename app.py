# app.py - SokoSwift KE Backend Logic

from flask import Flask, request, redirect, url_for, render_template, session, g
import sqlite3
import hashlib 
import os # Necessary for checking if the DB file exists on startup

app = Flask(__name__)
# IMPORTANT: Change this secret key in production!
app.secret_key = 'your_super_secret_key_CHANGE_ME' 
DATABASE = 'sokoswift.db' # SQLite database file name

# --- Database Helper Functions ---

def init_db():
    """Initializes the database structure from schema.sql."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Database initialized successfully.")

def get_db():
    """Opens a new database connection if one hasn't been established."""
    db = getattr(g, '_database', None)
    if db is None:
        # Check if the database file exists before connecting
        is_new = not os.path.exists(DATABASE) 
        
        # Connect to the database (will create the file if it doesn't exist)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        
        # If the file was just created (like on Render's first run), initialize the schema
        if is_new:
            print("Database file is new. Running initialization script.")
            init_db() 
            
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Security Helper ---

def hash_password(password):
    """Securely hashes a password (Placeholder for bcrypt)."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, password):
    """Checks a submitted password against the stored hash."""
    return hashed_password == hash_password(password)

# --- Cart Helper (SIMULATION ONLY) ---

def get_cart(session):
    """Simulates fetching cart items for demonstration/checkout."""
    # In a real app, this would query a dedicated cart table using session['user_id']
    return [
        {'product_id': 1, 'quantity': 2, 'unit_price': 2499.00, 'name': 'Pro Wireless Earbuds'}, 
        {'product_id': 3, 'quantity': 1, 'unit_price': 3200.00, 'name': 'Portable Bluetooth Speaker'}
    ]

# --- Routes ---

@app.route('/')
@app.route('/index')
def home():
    """Renders the main homepage (index.html). Redirects to login if not authenticated."""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        db = get_db()
        try:
            # Simple split for first and last name
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
            return redirect(url_for('login', success='Registration Successful! You can now log in.'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Email or Phone already registered.')
        except Exception as e:
            return render_template('register.html', error=f'An error occurred: {e}')
            
    return render_template('register.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login and session creation."""
    if request.method == 'POST':
        db = get_db()
        cursor = db.execute("SELECT * FROM Customers WHERE email = ?", (request.form['email'],))
        user = cursor.fetchone()

        if user and check_password(user['password_hash'], request.form['password']):
            session['logged_in'] = True
            session['user_id'] = user['customer_id']
            # Initialize cart count for the base template header
            session['cart_count'] = len(get_cart(session)) 
            return redirect(url_for('home