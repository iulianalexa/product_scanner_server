from flask import Flask, request, jsonify
import sqlite3

import uuid
import time
from werkzeug.security import check_password_hash

from functools import wraps

tokens = {}  # token -> (username, expiry)
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour

app = Flask(__name__)
DATABASE = 'data.db'
SCHEMA_FILE = 'schema.sql'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dict-like access to rows
    return conn

def init_db():
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DATABASE)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("Database initialized.")

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row['password_hash'], password):
        token = str(uuid.uuid4())
        expiry = time.time() + TOKEN_EXPIRY_SECONDS
        tokens[token] = (username, expiry)
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/sponsor', methods=['GET'])
def get_sponsors():
    count = int(request.args.get('count', 10))
    after = int(request.args.get('after', 0))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT sponsor_name, product_name, product_description, product_picture '
        'FROM sponsors '
        'LIMIT ? OFFSET ?', (count, after)
    )

    sponsors = cursor.fetchall()
    conn.close()

    sponsor_list = [dict(row) for row in sponsors]
    return jsonify(sponsor_list)

def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token not in tokens:
            return jsonify({'error': 'Unauthorized'}), 401
        username, expiry = tokens[token]
        if time.time() > expiry:
            del tokens[token]
            return jsonify({'error': 'Token expired'}), 401
        return f(*args, **kwargs)
    return wrapper
    
@app.route('/admin/protected', methods=['GET'])
@require_token
def protected_route():
    return jsonify({'message': 'Authorized access'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
