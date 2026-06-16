import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[OK] Database initialized")


def get_db_connection():
    """Get a connection to the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================
# USER MANAGEMENT
# ============================================

class User:
    """User model for database operations"""
    
    @staticmethod
    def create_user(username, email, password):
        """Create a new user
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Validate input
            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters"
            
            if not email or '@' not in email:
                return False, "Invalid email address"
            
            if not password or len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Insert into database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            
            conn.commit()
            conn.close()
            
            return True, "User registered successfully"
        
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return False, "Username already exists"
            elif 'email' in str(e):
                return False, "Email already registered"
            return False, "Registration failed"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate a user
        
        Returns:
            tuple: (success: bool, user_data: dict or message: str)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Find user by username
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "Invalid username or password"
            
            # Check password
            if not check_password_hash(user['password_hash'], password):
                conn.close()
                return False, "Invalid username or password"
            
            # Update last login
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()
            
            # Return user data (without password)
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
            return True, user_data
        
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return dict(user)
            return None
        
        except Exception as e:
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username, email FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return dict(user)
            return None
        
        except Exception as e:
            return None
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Change user password"""
        try:
            if not new_password or len(new_password) < 6:
                return False, "New password must be at least 6 characters"
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "User not found"
            
            # Verify old password
            if not check_password_hash(user['password_hash'], old_password):
                conn.close()
                return False, "Incorrect current password"
            
            # Update password
            new_hash = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
            conn.commit()
            conn.close()
            
            return True, "Password changed successfully"
        
        except Exception as e:
            return False, f"Error: {str(e)}"


# Initialize database on import
init_db()
