# Before Midnight Mall

A refined online storefront inspired by the previous midnight mall concept, redesigned with a cleaner access flow and a more professional retail experience.

## Key features

- Professional access page before entering the mall
- Product catalog with the same categories and products
- Cart and checkout flow
- Email notification to the store owner after each completed order
- Flask backend for product data and order processing

## Local run

1. Create a virtual environment
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Start the app

```bash
python server.py
```

4. Open:

```text
http://127.0.0.1:5000/
```

## Deploy notes

- Use the static storefront as the front-end on GitHub Pages
- Deploy the Flask backend on Render, Railway, or any Python host
- Update the frontend API URL in the script file to your deployed backend URL
