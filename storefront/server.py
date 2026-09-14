import json
import os
import random
import smtplib
import sqlite3
from datetime import datetime
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'after-midnight-mall-secret-key')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
)
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')
OWNER_EMAIL = os.getenv('OWNER_EMAIL', 'ericjuer@gmail.com').strip().lower()
OWNER_PASSWORD = os.getenv('OWNER_PASSWORD', 'midnight@1248').strip()


@app.after_request
def add_security_headers(response):
    origin = request.headers.get('Origin')
    allowed_origins = {
        'http://127.0.0.1:5000',
        'http://localhost:5000',
        'http://127.0.0.1',
        'http://localhost',
        'null',
    }

    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Vary'] = 'Origin'

    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                verification_code TEXT,
                approved_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT NOT NULL,
                shipping_name TEXT NOT NULL,
                shipping_email TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                shipping_city TEXT NOT NULL,
                shipping_postal_code TEXT NOT NULL,
                shipping_phone TEXT DEFAULT '',
                shipping_location TEXT DEFAULT '',
                payment_method TEXT DEFAULT 'cash_on_delivery',
                items_json TEXT NOT NULL,
                total REAL NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'queued'
            )
            """
        )

        order_columns = [row[1] for row in conn.execute('PRAGMA table_info(orders)').fetchall()]
        if 'shipping_phone' not in order_columns:
            conn.execute('ALTER TABLE orders ADD COLUMN shipping_phone TEXT DEFAULT ""')
        if 'shipping_location' not in order_columns:
            conn.execute('ALTER TABLE orders ADD COLUMN shipping_location TEXT DEFAULT ""')
        if 'payment_method' not in order_columns:
            conn.execute('ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT "cash_on_delivery"')


def email_valid(email: str) -> bool:
    return '@' in email and '.' in email.split('@')[-1]


def generate_code() -> str:
    return ''.join(random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))


def estimate_delivery_window(city: str):
    normalized = (city or '').strip().lower()
    fast_regions = {
        'new york': (3, 5),
        'brooklyn': (3, 5),
        'queens': (3, 5),
        'manhattan': (3, 5),
        'boston': (4, 6),
        'chicago': (4, 6),
        'miami': (4, 6),
        'atlanta': (3, 5),
        'dallas': (4, 6),
        'houston': (4, 6),
        'los angeles': (5, 7),
        'san francisco': (5, 8),
        'seattle': (5, 8),
    }
    return fast_regions.get(normalized, (5, 8))


def get_delivery_timeline(city: str):
    start_days, end_days = estimate_delivery_window(city)
    return {
        'city': (city or '').strip() or 'your city',
        'startDays': start_days,
        'endDays': end_days,
        'label': f'{start_days}-{end_days} business days',
    }


def send_verification_email(email: str, code: str) -> bool:
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    from_email = os.getenv('SMTP_FROM', 'no-reply@aftermidnightmall.local')

    if not smtp_host:
        print(f"[EMAIL SIMULATION] Verification code for {email}: {code}")
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = 'After Midnight Mall verification code'
        msg['From'] = from_email
        msg['To'] = email
        msg.set_content(
            f"Your After Midnight Mall verification code is: {code}\n\n"
            "Use this code in your verification request and wait for owner approval before logging in."
        )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"[EMAIL SENT] {email} -> {code}")
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {email}: {exc}")
        return False


def send_order_confirmation_email(order_id: int, customer_email: str, shipping_name: str, shipping_city: str,
                                 shipping_location: str, shipping_phone: str, payment_method: str,
                                 items: list, total: float) -> bool:
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    from_email = os.getenv('SMTP_FROM', 'no-reply@aftermidnightmall.local')

    items_text = ', '.join(f"{item.get('name', 'Item')} x {int(item.get('quantity', 0) or 0)}" for item in items)
    payment_label = 'Cash on delivery' if payment_method == 'cash_on_delivery' else payment_method.replace('_', ' ').title()

    if not smtp_host:
        print(
            f"[EMAIL SIMULATION] Order confirmation for {customer_email}: "
            f"Order #{order_id} - {items_text} - total TZS {total:.0f} - pay {payment_label} at delivery. "
            f"Location: {shipping_location}. Phone: {shipping_phone}."
        )
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = f'After Midnight Mall order confirmation #{order_id}'
        msg['From'] = from_email
        msg['To'] = customer_email
        msg.set_content(
            f"Hello {shipping_name},\n\n"
            f"Your order #{order_id} from After Midnight Mall has been confirmed.\n\n"
            f"Items: {items_text}\n"
            f"Total: TZS {total:.0f}\n"
            f"Delivery city: {shipping_city}\n"
            f"Exact location: {shipping_location}\n"
            f"Phone number: {shipping_phone}\n"
            f"Payment method: {payment_label}\n\n"
            "Please prepare cash for payment on delivery when the driver arrives. "
            "Your delivery team will contact you at the provided number if needed.\n\n"
            "Thank you for shopping with After Midnight Mall."
        )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"[EMAIL SENT] {customer_email} -> confirmation order #{order_id}")
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {customer_email}: {exc}")
        return False


@app.route('/')
def index_page():
    return send_from_directory('.', 'index.html')


@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')


@app.route('/admin.html')
def admin_page():
    return send_from_directory('.', 'admin.html')


@app.route('/index.html')
def storefront_page():
    return send_from_directory('.', 'index.html')


@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    verification_code_value = (data.get('verificationCode') or '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    if not email_valid(email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    verification_code = verification_code_value or generate_code()

    hashed_password = generate_password_hash(password)

    with get_db() as conn:
        existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({"error": "This email is already registered."}), 409

        conn.execute(
            """
            INSERT INTO users (email, password, verified, status, created_at, verification_code)
            VALUES (?, ?, 0, 'pending', ?, ?)
            """,
            (email, hashed_password, datetime.utcnow().isoformat(), verification_code),
        )

    email_sent = send_verification_email(email, verification_code)

    return jsonify({
        "message": (
            f"Verification email sent to {email}. "
            if email_sent else "Registration saved. Email delivery is not configured in this environment. "
        ) + "The owner must verify this account before login.",
        "email": email,
        "verificationCode": verification_code,
        "status": "pending",
    }), 201


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    with get_db() as conn:
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,),
        ).fetchone()

    if not user:
        return jsonify({"error": "Account not found. Please register first."}), 401
    if not user['verified']:
        return jsonify({"error": "This account is still waiting for owner verification."}), 403

    password_ok = user['password'] == password or check_password_hash(user['password'], password)
    if not password_ok:
        return jsonify({"error": "Incorrect password."}), 401

    if user['password'] == password and not user['password'].startswith('pbkdf2:'):
        hashed_password = generate_password_hash(password)
        with get_db() as conn:
            conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))

    session['customer_email'] = user['email']
    session['customer_logged_in'] = True

    return jsonify({
        "message": "Login successful.",
        "email": user['email'],
        "status": user['status'],
    }), 200


@app.route('/api/customer/status', methods=['GET'])
def customer_status():
    email = session.get('customer_email')
    return jsonify({
        "loggedIn": bool(session.get('customer_logged_in')),
        "email": email,
    })


@app.route('/api/customer/logout', methods=['POST'])
def customer_logout():
    session.pop('customer_email', None)
    session.pop('customer_logged_in', None)
    return jsonify({"message": "Logged out."})


@app.route('/api/owner/login', methods=['POST'])
def owner_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if email == OWNER_EMAIL and password == OWNER_PASSWORD:
        session['owner_logged_in'] = True
        session['owner_email'] = email
        return jsonify({"message": "Access granted."}), 200

    return jsonify({"error": "Invalid owner credentials."}), 401


@app.route('/api/owner/logout', methods=['POST'])
def owner_logout():
    session.pop('owner_logged_in', None)
    session.pop('owner_email', None)
    return jsonify({"message": "Logged out."})


@app.route('/api/owner/status', methods=['GET'])
def owner_status():
    return jsonify({"loggedIn": bool(session.get('owner_logged_in'))})


@app.route('/api/users', methods=['GET'])
def all_users():
    if not session.get('owner_logged_in'):
        return jsonify({"error": "Unauthorized."}), 401

    with get_db() as conn:
        rows = conn.execute(
            'SELECT email, verified, status, verification_code, created_at, approved_at FROM users ORDER BY created_at DESC'
        ).fetchall()

    return jsonify([
        {
            "email": row['email'],
            "verified": bool(row['verified']),
            "status": row['status'],
            "verificationCode": row['verification_code'],
            "createdAt": row['created_at'],
            "approvedAt": row['approved_at'],
        }
        for row in rows
    ])


@app.route('/api/users/pending', methods=['GET'])
def pending_users():
    if not session.get('owner_logged_in'):
        return jsonify({"error": "Unauthorized."}), 401

    with get_db() as conn:
        rows = conn.execute(
            'SELECT email, verification_code FROM users WHERE verified = 0 ORDER BY created_at DESC'
        ).fetchall()

    return jsonify([
        {"email": row['email'], "verificationCode": row['verification_code']} for row in rows
    ])


@app.route('/api/verify', methods=['POST'])
def verify_user():
    if not session.get('owner_logged_in'):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            return jsonify({"error": "User not found."}), 404

        conn.execute(
            'UPDATE users SET verified = 1, status = ?, approved_at = ?, verification_code = NULL WHERE email = ?',
            ('approved', datetime.utcnow().isoformat(), email),
        )

    return jsonify({"message": f"{email} has been approved and can now log in."})


@app.route('/api/orders', methods=['POST'])
def create_order():
    if not session.get('customer_logged_in'):
        return jsonify({"error": "Customer session required."}), 401

    data = request.get_json(silent=True) or {}
    items = data.get('items') or []
    shipping_name = (data.get('shippingName') or '').strip()
    shipping_email = (data.get('shippingEmail') or '').strip().lower()
    shipping_address = (data.get('shippingAddress') or '').strip()
    shipping_city = (data.get('shippingCity') or '').strip()
    shipping_postal_code = (data.get('shippingPostalCode') or '').strip()
    shipping_phone = (data.get('shippingPhone') or '').strip()
    shipping_location = (data.get('shippingLocation') or '').strip()
    payment_method = (data.get('paymentMethod') or 'cash_on_delivery').strip().lower()

    if not items or not shipping_name or not shipping_email or not shipping_address or not shipping_city or not shipping_postal_code:
        return jsonify({"error": "Complete shipping and order details are required."}), 400

    if payment_method not in {'cash_on_delivery', 'card', 'mobile_money'}:
        payment_method = 'cash_on_delivery'

    if payment_method == 'cash_on_delivery' and (not shipping_phone or not shipping_location):
        return jsonify({"error": "Phone number and exact delivery location are required for cash on delivery."}), 400

    total = 0.0
    for item in items:
        try:
            qty = int(item.get('quantity', 0) or 0)
            price = float(item.get('price', 0) or 0)
        except (TypeError, ValueError):
            return jsonify({"error": "Order items are invalid."}), 400
        if qty <= 0:
            return jsonify({"error": "Each item must have a quantity greater than zero."}), 400
        total += qty * price

    created_at = datetime.utcnow().isoformat()
    customer_email = session.get('customer_email', shipping_email)

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (
                customer_email, shipping_name, shipping_email, shipping_address, shipping_city,
                shipping_postal_code, shipping_phone, shipping_location, payment_method,
                items_json, total, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued')
            """,
            (
                customer_email,
                shipping_name,
                shipping_email,
                shipping_address,
                shipping_city,
                shipping_postal_code,
                shipping_phone,
                shipping_location,
                payment_method,
                json.dumps(items),
                round(total, 2),
                created_at,
            ),
        )
        order_id = cursor.lastrowid

    send_order_confirmation_email(
        order_id=order_id,
        customer_email=customer_email,
        shipping_name=shipping_name,
        shipping_city=shipping_city,
        shipping_location=shipping_location,
        shipping_phone=shipping_phone,
        payment_method=payment_method,
        items=items,
        total=round(total, 2),
    )

    delivery_timeline = get_delivery_timeline(shipping_city)

    return jsonify({
        "message": f"Order placed successfully. Please pay cash on delivery when the order arrives.",
        "orderId": order_id,
        "status": "queued",
        "total": round(total, 2),
        "customerEmail": customer_email,
        "shippingPhone": shipping_phone,
        "shippingLocation": shipping_location,
        "paymentMethod": payment_method,
        "deliveryTimeline": delivery_timeline,
    }), 201


@app.route('/api/orders', methods=['GET'])
def list_orders():
    if not session.get('owner_logged_in'):
        return jsonify({"error": "Unauthorized."}), 401

    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM orders ORDER BY created_at DESC'
        ).fetchall()

    return jsonify([
        {
            'id': row['id'],
            'customerEmail': row['customer_email'],
            'shippingName': row['shipping_name'],
            'shippingEmail': row['shipping_email'],
            'shippingAddress': row['shipping_address'],
            'shippingCity': row['shipping_city'],
            'shippingPostalCode': row['shipping_postal_code'],
            'items': json.loads(row['items_json']),
            'total': row['total'],
            'status': row['status'],
            'createdAt': row['created_at'],
            'deliveryTimeline': get_delivery_timeline(row['shipping_city']),
        }
        for row in rows
    ])


@app.route('/api/orders/me', methods=['GET'])
def list_my_orders():
    if not session.get('customer_logged_in'):
        return jsonify({"error": "Customer session required."}), 401

    customer_email = session.get('customer_email')
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM orders WHERE customer_email = ? ORDER BY created_at DESC',
            (customer_email,),
        ).fetchall()

    return jsonify([
        {
            'id': row['id'],
            'customerEmail': row['customer_email'],
            'shippingName': row['shipping_name'],
            'shippingEmail': row['shipping_email'],
            'shippingAddress': row['shipping_address'],
            'shippingCity': row['shipping_city'],
            'shippingPostalCode': row['shipping_postal_code'],
            'shippingPhone': row.get('shipping_phone', ''),
            'shippingLocation': row.get('shipping_location', ''),
            'paymentMethod': row.get('payment_method', 'cash_on_delivery'),
            'items': json.loads(row['items_json']),
            'total': row['total'],
            'status': row['status'],
            'createdAt': row['created_at'],
            'deliveryTimeline': get_delivery_timeline(row['shipping_city']),
        }
        for row in rows
    ])


@app.route('/api/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    if not session.get('owner_logged_in'):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').strip().lower()
    valid_statuses = {'queued', 'processing', 'shipped', 'delivered'}

    if not new_status or new_status not in valid_statuses:
        return jsonify({"error": "A valid order status is required."}), 400

    with get_db() as conn:
        existing = conn.execute('SELECT id FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Order not found."}), 404

        conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))

    return jsonify({"message": f"Order #{order_id} updated to {new_status}.", "status": new_status})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
