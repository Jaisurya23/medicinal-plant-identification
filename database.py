import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'users.db'

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with users table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create datasets table for file uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            uploaded_by TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create plants table for medicinal plants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_name TEXT UNIQUE NOT NULL,
            botanical_name TEXT NOT NULL,
            benefits TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database {DATABASE} initialized successfully.")

def create_user(username, email, name, password):
    """Register a new user with hashed password."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, name, password)
            VALUES (?, ?, ?, ?)
        ''', (username, email, name, hashed_password))
        
        conn.commit()
        conn.close()
        return True, "User registered successfully!"
    
    except sqlite3.IntegrityError as e:
        return False, f"Username or email already exists. {str(e)}"
    except Exception as e:
        return False, f"Error registering user: {str(e)}"

def get_user_by_username(username):
    """Fetch user details by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    conn.close()
    return user

def verify_password(username, password):
    """Verify user login credentials."""
    user = get_user_by_username(username)
    
    if user is None:
        return False, "User not found"
    
    if check_password_hash(user['password'], password):
        return True, user
    else:
        return False, "Invalid password"
    
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, name, created_at FROM users')
    users = cursor.fetchall()
    
    conn.close()
    return users

def save_dataset(filename, original_filename, file_path, file_size, uploaded_by):
    """Store uploaded dataset file metadata in database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO datasets (filename, original_filename, file_path, file_size, uploaded_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, original_filename, file_path, file_size, uploaded_by))
        
        conn.commit()
        conn.close()
        return True, "File uploaded successfully!"
    
    except Exception as e:
        return False, f"Error saving file: {str(e)}"

def get_all_datasets():
    """Fetch all uploaded datasets from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM datasets ORDER BY uploaded_at DESC')
    datasets = cursor.fetchall()
    
    conn.close()
    return datasets

def delete_dataset(dataset_id):
    """Delete a dataset record from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM datasets WHERE id = ?', (dataset_id,))
        
        conn.commit()
        conn.close()
        return True, "Dataset deleted successfully!"
    
    except Exception as e:
        return False, f"Error deleting dataset: {str(e)}"

def add_plant(plant_name, botanical_name, benefits):
    """Add a new medicinal plant to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO plants (plant_name, botanical_name, benefits)
            VALUES (?, ?, ?)
        ''', (plant_name, botanical_name, benefits))
        
        conn.commit()
        conn.close()
        return True, "Plant added successfully!"
    
    except sqlite3.IntegrityError:
        return False, "Plant name already exists. Please use a different name."
    except Exception as e:
        return False, f"Error adding plant: {str(e)}"

def get_all_plants():
    """Fetch all medicinal plants from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM plants ORDER BY plant_name ASC')
        plants = cursor.fetchall()
        
        conn.close()
        return plants
    except Exception as e:
        print(f"Error fetching plants: {str(e)}")
        return []

def get_plant_by_id(plant_id):
    """Fetch a specific plant by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM plants WHERE id = ?', (plant_id,))
        plant = cursor.fetchone()
        
        conn.close()
        return plant
    except Exception as e:
        print(f"Error fetching plant: {str(e)}")
        return None

def update_plant(plant_id, plant_name, botanical_name, benefits):
    """Update a medicinal plant record."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE plants 
            SET plant_name = ?, botanical_name = ?, benefits = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (plant_name, botanical_name, benefits, plant_id))
        
        conn.commit()
        conn.close()
        return True, "Plant updated successfully!"
    
    except sqlite3.IntegrityError:
        return False, "Plant name already exists. Please use a different name."
    except Exception as e:
        return False, f"Error updating plant: {str(e)}"

def delete_plant(plant_id):
    """Delete a medicinal plant from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
        
        conn.commit()
        conn.close()
        return True, "Plant deleted successfully!"
    
    except Exception as e:
        return False, f"Error deleting plant: {str(e)}"

def get_plant_by_name(plant_name):
    """Fetch a plant by name (case-insensitive, partial match)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try exact case-insensitive match first
        cursor.execute('SELECT * FROM plants WHERE LOWER(plant_name) = LOWER(?)', (plant_name,))
        plant = cursor.fetchone()
        
        if plant:
            conn.close()
            return plant
        
        # Try partial match if no exact match found
        cursor.execute('SELECT * FROM plants WHERE LOWER(plant_name) LIKE LOWER(?)', (f'%{plant_name}%',))
        plant = cursor.fetchone()
        
        conn.close()
        return plant
    except Exception as e:
        print(f"Error fetching plant by name: {str(e)}")
        return None
