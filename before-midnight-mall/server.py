import json
import os
import smtplib
import sqlite3
from datetime import datetime
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__, static_folder='.', static_url_path='')
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'before-midnight-mall-secret-key'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=False,
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'orders.db')
OWNER_EMAIL = os.getenv('OWNER_EMAIL', 'ericjuer@gmail.com').strip().lower()
ALLOWED_ORIGINS = {
    'http://127.0.0.1:5000',
    'http://localhost:5000',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://ericjuer-byte.github.io',
    'https://ericjuer-byte.github.io/special-mall',
    'null',
}

PRODUCTS = [
    {
        'id': 1,
        'name': 'Midnight Reverie Portrait',
        'price': 50000,
        'tag': 'Art',
        'category': 'Art',
        'rating': 4.9,
        'description': 'A moody, hand-crafted portrait designed to turn a wall into a cinematic evening statement.',
        'image': 'https://images.unsplash.com/photo-1515405295579-ba7b45403062?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 2,
        'name': 'Afterglow Echoes',
        'price': 50000,
        'tag': 'Art',
        'category': 'Art',
        'rating': 4.8,
        'description': 'A refined visual study that captures quiet after-hours emotion with timeless elegance.',
        'image': 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 3,
        'name': 'Love in Silver Light',
        'price': 50000,
        'tag': 'Art',
        'category': 'Art',
        'rating': 5.0,
        'description': 'A graceful expression of affection, crafted to feel intimate, warm, and deeply personal.',
        'image': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 4,
        'name': 'Eternal First Look',
        'price': 100000,
        'tag': 'Art',
        'category': 'Art',
        'rating': 4.7,
        'description': 'A luminous keepsake that preserves the beauty of a defining moment in a timeless form.',
        'image': 'https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 5,
        'name': 'Black Devil with a Bright Smile',
        'price': 10000,
        'tag': 'Refreshments',
        'category': 'Refreshments',
        'rating': 4.8,
        'description': 'A lively midnight refreshment with a bright citrus sparkle and smooth, feel-good finish.',
        'image': 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 6,
        'name': 'Velvet Ember Glow',
        'price': 5000,
        'tag': 'Refreshments',
        'category': 'Refreshments',
        'rating': 4.9,
        'description': 'A rich, smooth blend crafted for late-night rituals and elevated evening moments.',
        'image': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 7,
        'name': 'Midnight Velvet Tray',
        'price': 10000,
        'tag': 'Refreshments',
        'category': 'Refreshments',
        'rating': 4.7,
        'description': 'A cozy, elevated refreshment experience designed for relaxed evenings and warm escapes.',
        'image': 'https://images.unsplash.com/photo-1526312426976-f4d7548a8f6d?auto=format&fit=crop&w=900&q=80',
    },
    {
        'id': 8,
        'name': 'The Midnight Special',
        'price': 1000,
        'tag': 'Refreshments',
        'category': 'Refreshments',
        'rating': 4.9,
        'description': 'A crisp, mood-lifting favorite for a fresh reset and a refined after-dark unwind.',
        'image': 'https://images.unsplash.com/photo-1517701604599-bb5d7a0d2c3f?auto=format&fit=crop&w=900&q=80',
    },
]


@app.after_request
def add_security_headers(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
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
            '''
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
            '''
        )


def send_order_notification(order_id: int, customer_email: str, shipping_name: str, shipping_city: str, shipping_location: str,
                           shipping_phone: str, payment_method: str, items: list, total: float) -> bool:
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    from_email = os.getenv('SMTP_FROM', OWNER_EMAIL)

    items_text = ', '.join(f"{item.get('name', 'Item')} x {int(item.get('quantity', 0) or 0)}" for item in items)
    payment_label = 'Cash on delivery' if payment_method == 'cash_on_delivery' else payment_method.replace('_', ' ').title()

    if not smtp_host:
        print(f"[EMAIL SIMULATION] New order for {customer_email}: Order #{order_id} - {items_text} - total TZS {total:.0f} - {shipping_name} - {shipping_city} - {shipping_location} - {shipping_phone} - {payment_label}")
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = f'Before Midnight Mall order notification #{order_id}'
        msg['From'] = from_email
        msg['To'] = OWNER_EMAIL
        msg.set_content(
            f"Hello,\n\n"
            f"A new order was placed on Before Midnight Mall.\n\n"
            f"Order #: {order_id}\n"
            f"Customer: {shipping_name}\n"
            f"Customer email: {customer_email}\n"
            f"Items: {items_text}\n"
            f"Total: TZS {total:.0f}\n"
            f"City: {shipping_city}\n"
            f"Exact location: {shipping_location}\n"
            f"Phone: {shipping_phone}\n"
            f"Payment method: {payment_label}\n\n"
            "Please prepare the package and confirm this order with the customer."
        )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"[EMAIL SENT] Owner notified about order #{order_id}")
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}")
        return False


@app.route('/')
def access_page():
    return send_from_directory('.', 'access.html')


@app.route('/access.html')
def access_html():
    return send_from_directory('.', 'access.html')


@app.route('/index.html')
def mall_page():
    return send_from_directory('.', 'index.html')


@app.route('/api/products')
def api_products():
    return jsonify(PRODUCTS)


@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json(silent=True) or {}
    items = data.get('items') or []
    if not isinstance(items, list) or not items:
        return jsonify({'error': 'Your cart is empty.'}), 400

    shipping_name = (data.get('shippingName') or '').strip()
    shipping_email = (data.get('shippingEmail') or '').strip()
    shipping_address = (data.get('shippingAddress') or '').strip()
    shipping_city = (data.get('shippingCity') or '').strip()
    shipping_postal_code = (data.get('shippingPostalCode') or '').strip()
    shipping_phone = (data.get('shippingPhone') or '').strip()
    shipping_location = (data.get('shippingLocation') or '').strip()
    payment_method = (data.get('paymentMethod') or 'cash_on_delivery').strip()

    if not all([shipping_name, shipping_email, shipping_address, shipping_city, shipping_postal_code, shipping_phone, shipping_location]):
        return jsonify({'error': 'Please fill in all delivery details.'}), 400

    subtotal = 0.0
    for item in items:
        product = next((p for p in PRODUCTS if p['id'] == int(item.get('id', 0))), None)
        if not product:
            return jsonify({'error': 'One or more products are invalid.'}), 400
        subtotal += float(product['price']) * int(item.get('quantity', 0) or 0)

    shipping_fee = 0 if subtotal >= 150000 else 12000
    total = subtotal + shipping_fee

    with get_db() as conn:
        cursor = conn.execute(
            '''
            INSERT INTO orders (
                customer_email, shipping_name, shipping_email, shipping_address, shipping_city,
                shipping_postal_code, shipping_phone, shipping_location, payment_method,
                items_json, total, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                shipping_email,
                shipping_name,
                shipping_email,
                shipping_address,
                shipping_city,
                shipping_postal_code,
                shipping_phone,
                shipping_location,
                payment_method,
                json.dumps(items),
                total,
                datetime.utcnow().isoformat(),
                'queued',
            ),
        )
        order_id = cursor.lastrowid

    send_order_notification(
        order_id=order_id,
        customer_email=shipping_email,
        shipping_name=shipping_name,
        shipping_city=shipping_city,
        shipping_location=shipping_location,
        shipping_phone=shipping_phone,
        payment_method=payment_method,
        items=items,
        total=total,
    )

    return jsonify({
        'message': 'Order placed successfully. A confirmation email has been sent.',
        'orderId': order_id,
        'total': total,
        'status': 'queued',
    }), 201


@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'service': 'before-midnight-mall'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=True)
