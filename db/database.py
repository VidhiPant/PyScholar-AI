import sqlite3
import os

# FORCE ABSOLUTE PATH to avoid "table not found" errors
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bookings.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database with the required tables."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Create Customers Table
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  email TEXT, 
                  phone TEXT)''')
    
    # 2. Create Bookings Table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer_id INTEGER, 
                  booking_type TEXT, 
                  date TEXT, 
                  time TEXT, 
                  status TEXT,
                  FOREIGN KEY(customer_id) REFERENCES customers(id))''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def add_booking(name, email, phone, booking_type, date, time):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if customer exists, else create
        c.execute("SELECT id FROM customers WHERE email = ?", (email,))
        data = c.fetchone()
        
        if data:
            customer_id = data[0]
        else:
            c.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
            customer_id = c.lastrowid
            
        # Insert Booking
        c.execute("INSERT INTO bookings (customer_id, booking_type, date, time, status) VALUES (?, ?, ?, ?, 'Confirmed')", 
                  (customer_id, booking_type, date, time))
        conn.commit()
        return True, c.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()