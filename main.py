from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'sponsors.db'
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


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
