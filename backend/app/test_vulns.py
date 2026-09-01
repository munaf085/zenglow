import os
import sqlite3
import hashlib
import pickle
import requests
import xml.etree.ElementTree as ET

# 1. Hardcoded Secret
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"

def get_user_data(user_id):
    # 2. SQL Injection
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchall()

def read_file(filename):
    # 3. Path Traversal
    filepath = f"/var/www/uploads/{filename}"
    with open(filepath, 'r') as f:
        return f.read()

def ping_server(ip_address):
    # 4. Command Injection
    os.system(f"ping -c 4 {ip_address}")

def render_welcome(user_name):
    # 5. Cross-Site Scripting (XSS)
    return f"<html><body><h1>Welcome, {user_name}!</h1></body></html>"

def load_user_session(session_data):
    # 6. Insecure Deserialization
    return pickle.loads(session_data)

def fetch_external_url(url):
    # 7. Server-Side Request Forgery (SSRF)
    response = requests.get(url)
    return response.text

def hash_password(password):
    # 8. Weak Hashing Algorithm (MD5)
    return hashlib.md5(password.encode()).hexdigest()

def delete_user(user, target_id):
    # 9. Improper Authorization (Using assert in production)
    assert user.is_admin, "User must be an admin"
    # Logic to delete user...
    pass

def parse_xml_data(xml_string):
    # 10. XML External Entity (XXE) Vulnerability
    tree = ET.parse(xml_string)
    return tree.getroot()
