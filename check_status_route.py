from storefront.server import app, init_db, get_db

app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'
init_db()
with get_db() as conn:
    conn.execute('DELETE FROM orders')
    conn.execute('DELETE FROM users')
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'users'")
    conn.execute(
        '''
        INSERT INTO orders (customer_email, shipping_name, shipping_email, shipping_address, shipping_city, shipping_postal_code, items_json, total, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        ('status-test@example.com', 'Status Buyer', 'status-test@example.com', '456 Market Street', 'Boston', '02110', '[{"id": 2, "name": "Drift Throw", "price": 64, "quantity": 1}]', 64.0, '2026-01-01T00:00:00', 'queued'),
    )
    conn.execute(
        'INSERT INTO users (email, password, verified, status, created_at, verification_code) VALUES (?, ?, 1, ?, ?, NULL)',
        ('status-test@example.com', 'hash', 'approved', '2026-01-01T00:00:00'),
    )

client = app.test_client()
with client.session_transaction() as sess:
    sess['owner_logged_in'] = True
    sess['owner_email'] = 'owner@aftermidnightmall.com'

response = client.patch('/api/orders/1/status', json={'status': 'shipped'})
print('status_code=', response.status_code)
print('json=', response.get_json())
