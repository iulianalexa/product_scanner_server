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
    
# Test admin route
@app.route('/admin/protected', methods=['GET'])
@require_token
def protected_route():
    return jsonify({'message': 'Authorized access'})

@app.route('/admin/ingredients', methods=['GET'])
@require_token
def list_ingredients():
    count = int(request.args.get('count', 10))
    after = int(request.args.get('after', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, description FROM ingredients '
        'LIMIT ? OFFSET ?', (count, after)
    )
    ingredients = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in ingredients])

@app.route('/admin/ingredient', methods=['POST'])
@require_token
def create_ingredient():
    data = request.json
    name = data.get('name')
    description = data.get('description')

    if not name or not description:
        return jsonify({'error': 'Missing name or description'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ingredients (name, description) VALUES (?, ?)', (name, description))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ingredient created'}), 201

@app.route('/admin/ingredient/<int:ingredient_id>', methods=['PUT'])
@require_token
def edit_ingredient(ingredient_id):
    data = request.json
    name = data.get('name')
    description = data.get('description')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE ingredients SET name = ?, description = ? WHERE id = ?',
        (name, description, ingredient_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'status': 'ingredient updated'})

@app.route('/admin/ingredient/<int:ingredient_id>', methods=['DELETE'])
@require_token
def delete_ingredient(ingredient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ingredients WHERE id = ?', (ingredient_id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ingredient deleted'})

@app.route('/admin/sponsor', methods=['POST'])
@require_token
def create_sponsor():
    data = request.json
    sponsor_name = data.get('sponsor_name')
    product_name = data.get('product_name')
    product_description = data.get('product_description')
    product_picture = data.get('product_picture')

    if not all([sponsor_name, product_name, product_description, product_picture]):
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sponsors (sponsor_name, product_name, product_description, product_picture) '
        'VALUES (?, ?, ?, ?)',
        (sponsor_name, product_name, product_description, product_picture)
    )
    conn.commit()
    conn.close()

    return jsonify({'status': 'sponsor product created'}), 201

@app.route('/admin/sponsor/<int:sponsor_id>', methods=['PUT'])
@require_token
def edit_sponsor(sponsor_id):
    data = request.json
    sponsor_name = data.get('sponsor_name')
    product_name = data.get('product_name')
    product_description = data.get('product_description')
    product_picture = data.get('product_picture')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE sponsors SET sponsor_name = ?, product_name = ?, product_description = ?, product_picture = ? '
        'WHERE id = ?',
        (sponsor_name, product_name, product_description, product_picture, sponsor_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'status': 'sponsor product updated'})

@app.route('/admin/sponsor/<int:sponsor_id>', methods=['DELETE'])
@require_token
def delete_sponsor(sponsor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sponsors WHERE id = ?', (sponsor_id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'sponsor product deleted'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
