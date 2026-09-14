import os
import unittest

from flask import session

from storefront.server import app, get_db, init_db
from werkzeug.security import check_password_hash


class AfterMidnightMallAppTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        init_db()
        with get_db() as conn:
            conn.execute('DELETE FROM orders')
            conn.execute('DELETE FROM users')
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'users'")
        self.client = app.test_client()

    def test_registration_hashes_password(self):
        email = 'hash-test@example.com'
        password = 'StrongPass123!'

        response = self.client.post('/api/register', json={'email': email, 'password': password})
        self.assertEqual(response.status_code, 201)

        with get_db() as conn:
            user = conn.execute('SELECT password FROM users WHERE email = ?', (email,)).fetchone()

        self.assertIsNotNone(user)
        self.assertNotEqual(user['password'], password)
        self.assertTrue(check_password_hash(user['password'], password))

    def test_customer_can_submit_order(self):
        email = 'order-test@example.com'
        password = 'StrongPass123!'
        self.client.post('/api/register', json={'email': email, 'password': password})

        with get_db() as conn:
            conn.execute('UPDATE users SET verified = 1, status = ? WHERE email = ?', ('approved', email))

        login_response = self.client.post('/api/login', json={'email': email, 'password': password})
        self.assertEqual(login_response.status_code, 200)

        response = self.client.post(
            '/api/orders',
            json={
                'items': [{'id': 1, 'name': 'After Dark Lamp', 'price': 89, 'quantity': 1}],
                'shippingName': 'Sample Customer',
                'shippingEmail': email,
                'shippingAddress': '123 Market Street',
                'shippingCity': 'New York',
                'shippingPostalCode': '10001',
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIn('orderId', payload)

    def test_owner_can_update_order_status(self):
        email = 'status-test@example.com'
        password = 'StrongPass123!'
        self.client.post('/api/register', json={'email': email, 'password': password})

        with get_db() as conn:
            conn.execute('UPDATE users SET verified = 1, status = ? WHERE email = ?', ('approved', email))
            conn.execute(
                '''
                INSERT INTO orders (customer_email, shipping_name, shipping_email, shipping_address, shipping_city, shipping_postal_code, items_json, total, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (email, 'Status Buyer', email, '456 Market Street', 'Boston', '02110', '[{"id": 2, "name": "Drift Throw", "price": 64, "quantity": 1}]', 64.0, '2026-01-01T00:00:00', 'queued'),
            )
            order = conn.execute('SELECT id FROM orders WHERE customer_email = ? ORDER BY id DESC LIMIT 1', (email,)).fetchone()

        self.assertIsNotNone(order)
        order_id = order['id']

        with self.client.session_transaction() as sess:
            sess['owner_logged_in'] = True
            sess['owner_email'] = 'owner@aftermidnightmall.com'

        response = self.client.patch(f'/api/orders/{order_id}/status', json={'status': 'shipped'})
        self.assertEqual(response.status_code, 200)

        with get_db() as conn:
            status = conn.execute('SELECT status FROM orders WHERE id = ?', (order_id,)).fetchone()

        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'shipped')

    def test_customer_can_view_their_order_history(self):
        email = 'history-test@example.com'
        password = 'StrongPass123!'
        self.client.post('/api/register', json={'email': email, 'password': password})

        with get_db() as conn:
            conn.execute('UPDATE users SET verified = 1, status = ? WHERE email = ?', ('approved', email))
            conn.execute(
                '''
                INSERT INTO orders (customer_email, shipping_name, shipping_email, shipping_address, shipping_city, shipping_postal_code, items_json, total, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (email, 'History Buyer', email, '789 Market Street', 'Chicago', '60601', '[{"id": 3, "name": "Haven Mug", "price": 26, "quantity": 2}]', 52.0, '2026-02-01T00:00:00', 'queued'),
            )

        with self.client.session_transaction() as sess:
            sess['customer_logged_in'] = True
            sess['customer_email'] = email

        response = self.client.get('/api/orders/me')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(isinstance(payload, list))
        self.assertGreaterEqual(len(payload), 1)
        self.assertEqual(payload[0]['customerEmail'], email)

    def test_customer_order_history_includes_city_based_delivery_timeline(self):
        email = 'timeline-test@example.com'
        password = 'StrongPass123!'
        self.client.post('/api/register', json={'email': email, 'password': password})

        with get_db() as conn:
            conn.execute('UPDATE users SET verified = 1, status = ? WHERE email = ?', ('approved', email))
            conn.execute(
                '''
                INSERT INTO orders (customer_email, shipping_name, shipping_email, shipping_address, shipping_city, shipping_postal_code, items_json, total, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (email, 'Timeline Buyer', email, '999 Market Street', 'Seattle', '98101', '[{"id": 4, "name": "Night Glass", "price": 120, "quantity": 1}]', 120.0, '2026-03-01T00:00:00', 'queued'),
            )

        with self.client.session_transaction() as sess:
            sess['customer_logged_in'] = True
            sess['customer_email'] = email

        response = self.client.get('/api/orders/me')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload)
        self.assertEqual(payload[0]['shippingCity'], 'Seattle')
        self.assertIn('deliveryTimeline', payload[0])
        self.assertEqual(payload[0]['deliveryTimeline']['city'], 'Seattle')
        self.assertIn('business days', payload[0]['deliveryTimeline']['label'])

    def test_customer_can_submit_cash_on_delivery_order_with_location_and_phone(self):
        email = 'cash-test@example.com'
        password = 'StrongPass123!'
        self.client.post('/api/register', json={'email': email, 'password': password})

        with get_db() as conn:
            conn.execute('UPDATE users SET verified = 1, status = ? WHERE email = ?', ('approved', email))

        with self.client.session_transaction() as sess:
            sess['customer_logged_in'] = True
            sess['customer_email'] = email

        response = self.client.post(
            '/api/orders',
            json={
                'items': [{'id': 8, 'name': 'The Midnight Special', 'price': 1000, 'quantity': 1}],
                'shippingName': 'Cash Buyer',
                'shippingEmail': email,
                'shippingAddress': 'Mbezi Beach Road',
                'shippingCity': 'Dar es Salaam',
                'shippingPostalCode': '12345',
                'shippingPhone': '+255712345678',
                'shippingLocation': 'Mbezi Beach, Plot 14, House 7',
                'paymentMethod': 'cash_on_delivery',
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload['paymentMethod'], 'cash_on_delivery')
        self.assertEqual(payload['shippingPhone'], '+255712345678')
        self.assertEqual(payload['shippingLocation'], 'Mbezi Beach, Plot 14, House 7')
        self.assertIn('cash on delivery', payload['message'].lower())

        with get_db() as conn:
            order = conn.execute(
                'SELECT shipping_phone, shipping_location, payment_method FROM orders WHERE customer_email = ? ORDER BY id DESC LIMIT 1',
                (email,),
            ).fetchone()

        self.assertIsNotNone(order)
        self.assertEqual(order['shipping_phone'], '+255712345678')
        self.assertEqual(order['shipping_location'], 'Mbezi Beach, Plot 14, House 7')
        self.assertEqual(order['payment_method'], 'cash_on_delivery')


if __name__ == '__main__':
    unittest.main()
