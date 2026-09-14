const API_BASE = 'http://127.0.0.1:5000';

const products = [
  {
    id: 1,
    name: 'Midnight Reverie Portrait',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 4.9,
    description: 'A moody, hand-crafted portrait designed to turn a wall into a cinematic evening statement.',
    image: 'https://images.unsplash.com/photo-1515405295579-ba7b45403062?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 2,
    name: 'Afterglow Echoes',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 4.8,
    description: 'A refined visual study that captures quiet after-hours emotion with timeless elegance.',
    image: 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 3,
    name: 'Love in Silver Light',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 5.0,
    description: 'A graceful expression of affection, crafted to feel intimate, warm, and deeply personal.',
    image: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 4,
    name: 'Eternal First Look',
    price: 100000,
    tag: 'Art',
    category: 'Art',
    rating: 4.7,
    description: 'A luminous keepsake that preserves the beauty of a defining moment in a timeless form.',
    image: 'https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 5,
    name: 'Black Devil with a Bright Smile',
    price: 10000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.8,
    description: 'A lively midnight refreshment with a bright citrus sparkle and smooth, feel-good finish.',
    image: 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 6,
    name: 'Velvet Ember Glow',
    price: 5000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.9,
    description: 'A rich, smooth blend crafted for late-night rituals and elevated evening moments.',
    image: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 7,
    name: 'Midnight Velvet Tray',
    price: 10000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.7,
    description: 'A cozy, elevated refreshment experience designed for relaxed evenings and warm escapes.',
    image: 'https://images.unsplash.com/photo-1526312426976-f4d7548a8f6d?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 8,
    name: 'The Midnight Special',
    price: 1000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.9,
    description: 'A crisp, mood-lifting favorite for a fresh reset and a refined after-dark unwind.',
    image: 'https://images.unsplash.com/photo-1517701604599-bb5d7a0d2c3f?auto=format&fit=crop&w=900&q=80',
  },
];

const cart = [];

const productGrid = document.getElementById('productGrid');
const cartPanel = document.getElementById('cartPanel');
const cartItems = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const subtotalEl = document.getElementById('subtotal');
const shippingEl = document.getElementById('shipping');
const totalEl = document.getElementById('total');
const checkoutModalBackdrop = document.getElementById('checkoutModalBackdrop');
const checkoutForm = document.getElementById('checkoutForm');
const checkoutTotal = document.getElementById('checkoutTotal');
const customerStatus = document.getElementById('customerStatus');
const guestLogoutBtn = document.getElementById('guestLogoutBtn');

function getGuestProfile() {
  const stored = localStorage.getItem('beforeMidnightMallGuest');
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch (error) {
    return null;
  }
}

function applyGuestStatus() {
  const guest = getGuestProfile();
  if (!guest) {
    window.location.href = 'access.html';
    return;
  }

  customerStatus.textContent = guest.name || 'Guest';
  guestLogoutBtn.style.display = 'inline-flex';
}

function getProductById(productId) {
  return products.find((product) => product.id === productId);
}

function renderProducts() {
  productGrid.innerHTML = products
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-image">
            <img src="${product.image}" alt="${product.name}" />
            <span class="product-badge">${product.tag}</span>
          </div>
          <div class="product-copy">
            <div class="product-head">
              <h3>${product.name}</h3>
              <span class="price">TZS ${product.price.toLocaleString()}</span>
            </div>
            <p class="product-category">${product.category}</p>
            <p>${product.description}</p>
            <div class="product-meta">
              <span class="rating">★ ${product.rating}</span>
              <button class="add-btn" data-product-id="${product.id}">Add to cart</button>
            </div>
          </div>
        </article>
      `,
    )
    .join('');

  document.querySelectorAll('.add-btn').forEach((button) => {
    button.addEventListener('click', (event) => {
      addToCart(Number(event.currentTarget.dataset.productId));
    });
  });
}

function addToCart(productId) {
  const existingItem = cart.find((item) => item.id === productId);

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ id: productId, quantity: 1 });
  }

  renderCart();
}

function changeQuantity(productId, delta) {
  const item = cart.find((entry) => entry.id === productId);

  if (!item) return;

  item.quantity += delta;

  if (item.quantity <= 0) {
    const index = cart.findIndex((entry) => entry.id === productId);
    cart.splice(index, 1);
  }

  renderCart();
}

function renderCart() {
  if (!cart.length) {
    cartItems.innerHTML = '<p class="empty-cart">Your cart is empty.</p>';
  } else {
    cartItems.innerHTML = cart
      .map((item) => {
        const product = getProductById(item.id);
        return `
          <div class="cart-item">
            <img src="${product.image}" alt="${product.name}" />
            <div>
              <h4>${product.name}</h4>
              <p>${product.tag}</p>
              <div class="item-controls">
                <button class="qty-btn" data-action="decrease" data-product-id="${product.id}">−</button>
                <span>${item.quantity}</span>
                <button class="qty-btn" data-action="increase" data-product-id="${product.id}">+</button>
              </div>
            </div>
            <span class="item-price">TZS ${(product.price * item.quantity).toLocaleString()}</span>
          </div>
        `;
      })
      .join('');
  }

  document.querySelectorAll('.qty-btn').forEach((button) => {
    button.addEventListener('click', (event) => {
      const productId = Number(event.currentTarget.dataset.productId);
      const action = event.currentTarget.dataset.action;
      changeQuantity(productId, action === 'increase' ? 1 : -1);
    });
  });

  const itemCount = cart.reduce((total, item) => total + item.quantity, 0);
  cartCount.textContent = String(itemCount);

  const subtotal = cart.reduce((total, item) => {
    const product = getProductById(item.id);
    return total + product.price * item.quantity;
  }, 0);

  const shipping = subtotal >= 150000 || subtotal === 0 ? 0 : 12000;
  const total = subtotal + shipping;

  subtotalEl.textContent = `TZS ${subtotal.toLocaleString()}`;
  shippingEl.textContent = `TZS ${shipping.toLocaleString()}`;
  totalEl.textContent = `TZS ${total.toLocaleString()}`;

  checkoutTotal.textContent = `TZS ${total.toLocaleString()}`;
}

function openCheckoutModal() {
  if (!cart.length) {
    alert('Your cart is empty. Add a few favorites first.');
    return;
  }

  checkoutModalBackdrop.classList.add('open');
  checkoutModalBackdrop.setAttribute('aria-hidden', 'false');
}

function closeCheckoutModal() {
  checkoutModalBackdrop.classList.remove('open');
  checkoutModalBackdrop.setAttribute('aria-hidden', 'true');
  checkoutForm.reset();
}

async function placeOrder(payload) {
  const response = await fetch(`${API_BASE}/api/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.error || 'Order could not be submitted.');
  }

  return body;
}

cartToggleButton.addEventListener('click', () => {
  cartPanel.classList.add('open');
});

document.querySelector('.close-cart').addEventListener('click', () => {
  cartPanel.classList.remove('open');
});

document.querySelector('.close-checkout').addEventListener('click', closeCheckoutModal);
checkoutModalBackdrop.addEventListener('click', (event) => {
  if (event.target === checkoutModalBackdrop) {
    closeCheckoutModal();
  }
});

document.querySelector('.checkout-btn').addEventListener('click', openCheckoutModal);

checkoutForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(checkoutForm);
  const payload = {
    items: cart.map((item) => {
      const product = getProductById(item.id);
      return {
        id: item.id,
        name: product.name,
        price: product.price,
        quantity: item.quantity,
      };
    }),
    shippingName: formData.get('fullName')?.toString().trim(),
    shippingEmail: formData.get('email')?.toString().trim(),
    shippingAddress: formData.get('address')?.toString().trim(),
    shippingCity: formData.get('city')?.toString().trim(),
    shippingPostalCode: formData.get('postalCode')?.toString().trim(),
    shippingPhone: formData.get('phone')?.toString().trim(),
    shippingLocation: formData.get('location')?.toString().trim(),
    paymentMethod: 'cash_on_delivery',
  };

  if (!payload.shippingName || !payload.shippingEmail || !payload.shippingAddress || !payload.shippingCity || !payload.shippingPostalCode || !payload.shippingPhone || !payload.shippingLocation) {
    alert('Please complete all delivery details before placing the order.');
    return;
  }

  if (!cart.length) {
    alert('Your cart is empty. Add a few favorites before checking out.');
    return;
  }

  try {
    const result = await placeOrder(payload);
    alert(`Thank you, ${payload.shippingName}! Your order for TZS ${Number(result.total || 0).toLocaleString()} has been placed successfully. A confirmation email will be sent to ${payload.shippingEmail}.`);
    cart.length = 0;
    renderCart();
    closeCheckoutModal();
    cartPanel.classList.remove('open');
  } catch (error) {
    alert(error.message || 'An error occurred while placing the order.');
  }
});

guestLogoutBtn.addEventListener('click', () => {
  localStorage.removeItem('beforeMidnightMallGuest');
  window.location.href = 'access.html';
});

applyGuestStatus();
renderProducts();
renderCart();
