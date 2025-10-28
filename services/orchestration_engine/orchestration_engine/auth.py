# services/orchestration_engine/orchestration_engine/auth.py

import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
from .database import get_db_connection, hash_password, check_password

# This should be a strong, secret key stored securely (e.g., in an env var)
SECRET_KEY = "your-super-secret-key"

def register_user(username, password):
    """Registers a new user."""
    db = get_db_connection()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        db.commit()
        return True
    except db.IntegrityError:  # This will trigger if the username is already taken
        return False
    finally:
        db.close()

def authenticate_user(username, password):
    """Authenticates a user and returns a JWT if successful."""
    db = get_db_connection()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()

    if user and check_password(user['password_hash'], password):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return token
    return None

def token_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            db = get_db_connection()
            g.current_user = db.execute("SELECT * FROM users WHERE id = ?", (data['user_id'],)).fetchone()
            db.close()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        if g.current_user is None:
            return jsonify({'message': 'User not found!'}), 401

        return f(*args, **kwargs)

    return decorated
