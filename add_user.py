import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'data.db'

def add_user(username, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"User '{username}' added.")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    import getpass
    u = input("Username: ")
    p = getpass.getpass("Password: ")
    add_user(u, p)

