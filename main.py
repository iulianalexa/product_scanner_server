from flask import Flask, request, jsonify
import sqlite3

import uuid
import time
from werkzeug.security import check_password_hash

from functools import wraps

import re

import logging

from flask import g

admin_logger = logging.getLogger('admin_logger')
admin_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('admin_actions.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

admin_logger.addHandler(file_handler)
def log_action(username, action, details):
    admin_logger.info(f"{username} {action}: {details}")

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
    
@app.route('/ingredients', methods=['POST'])
def scan_ingredients():
    data = request.get_json()
    input_text = data.get('text', '').lower()

    if not input_text.strip():
        return jsonify({'error': 'Text input is required'}), 400

    # Tokenize input string into unique lowercase words
    words = set(re.findall(r'\b\w+\b', input_text))
    if not words:
        return jsonify({'matched_ingredients': [], 'average_score': 0.0})

    placeholders = ','.join('?' for _ in words)

    query = f'''
        SELECT id, name, description, ingredient_score
        FROM ingredients
        WHERE LOWER(name) IN ({placeholders})
    '''

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, list(words))
    matched_rows = cursor.fetchall()
    conn.close()

    matched = []
    total_score = 0.0

    for row in matched_rows:
        matched.append({
            'ingredient_id': row['id'],
            'ingredient_name': row['name'],
            'ingredient_description': row['description'],
            'ingredient_score': row['ingredient_score']
        })
        total_score += row['ingredient_score']

    average_score = round(total_score / len(matched), 2) if matched else 0.0

    return jsonify({
        'matched_ingredients': matched,
        'average_score': average_score
    })

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
        g.username = username  # attach username to request context
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
        'SELECT id, name, description, ingredient_score FROM ingredients '
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
    score = data.get('ingredient_score', 0.0)

    if not name or not description:
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO ingredients (name, description, ingredient_score) VALUES (?, ?, ?)',
        (name, description, score)
    )
    conn.commit()
    conn.close()
    
    log_action(g.username, "created ingredient", f"{name}, score={score}")
    
    return jsonify({'status': 'ingredient created'})

@app.route('/admin/ingredient/<int:id>', methods=['PUT'])
@require_token
def edit_ingredient(id):
    data = request.json
    name = data.get('name')
    description = data.get('description')
    score = data.get('ingredient_score', 0.0)

    conn = get_db_connection()
    conn.execute(
        'UPDATE ingredients SET name = ?, description = ?, ingredient_score = ? WHERE id = ?',
        (name, description, score, id)
    )
    conn.commit()
    conn.close()
    
    log_action(g.username, "edited ingredient", f"id={id}, name={name}, score={score}")
    
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
    
    log_action(g.username, "deleted ingredient", f"id={ingredient_id}")

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
    
    log_action(g.username, "edited sponsor", f"id={sponsor_id}, name={sponsor_name}, product_name={product_name}, product_description={product_description}, product_picture={product_picture}")

    return jsonify({'status': 'sponsor product updated'})

@app.route('/admin/sponsor/<int:sponsor_id>', methods=['DELETE'])
@require_token
def delete_sponsor(sponsor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sponsors WHERE id = ?', (sponsor_id,))
    conn.commit()
    conn.close()
    
    log_action(g.username, "deleted sponsor", f"id={sponsor_id}")

    return jsonify({'status': 'sponsor product deleted'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
