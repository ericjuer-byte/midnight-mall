function createProductPlaceholder(title, accent, accent2) {
  const svg = `
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 720'>
      <defs>
        <linearGradient id='bg' x1='0' x2='1' y1='0' y2='1'>
          <stop offset='0%' stop-color='${accent}'/>
          <stop offset='100%' stop-color='${accent2}'/>
        </linearGradient>
      </defs>
      <rect width='800' height='720' fill='url(#bg)'/>
      <circle cx='640' cy='150' r='90' fill='rgba(255,255,255,0.18)'/>
      <circle cx='140' cy='590' r='130' fill='rgba(0,0,0,0.12)'/>
      <path d='M200 560C290 420 510 390 620 510V720H200Z' fill='rgba(11,11,18,0.18)'/>
      <rect x='90' y='90' width='620' height='540' rx='32' fill='rgba(12,15,24,0.18)' stroke='rgba(255,255,255,0.18)'/>
      <text x='400' y='340' text-anchor='middle' fill='rgba(255,255,255,0.8)' font-size='48' font-family='Arial, sans-serif' font-weight='700'>${title}</text>
      <text x='400' y='390' text-anchor='middle' fill='rgba(255,255,255,0.7)' font-size='24' font-family='Arial, sans-serif'>Product showcase</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

const products = [
  {
    id: 1,
    name: 'Midnight Reverie Portrait',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 4.9,
    description: 'A moody, hand-crafted portrait designed to turn a wall into a cinematic evening statement.',
    image: 'product-images/product-1.jpg',
    fallback: createProductPlaceholder('Midnight Reverie', '#26163f', '#7b5cf1'),
  },
  {
    id: 2,
    name: 'Afterglow Echoes',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 4.8,
    description: 'A refined visual study that captures quiet after-hours emotion with timeless elegance.',
    image: 'product-images/product-2.jpg',
    fallback: createProductPlaceholder('Afterglow Echoes', '#3f1d2a', '#ef9d7b'),
  },
  {
    id: 3,
    name: 'Love in Silver Light',
    price: 50000,
    tag: 'Art',
    category: 'Art',
    rating: 5.0,
    description: 'A graceful expression of affection, crafted to feel intimate, warm, and deeply personal.',
    image: 'product-images/product-3.jpg',
    fallback: createProductPlaceholder('Silver Light', '#171d2d', '#4d6ef0'),
  },
  {
    id: 4,
    name: 'Eternal First Look',
    price: 100000,
    tag: 'Art',
    category: 'Art',
    rating: 4.7,
    description: 'A luminous keepsake that preserves the beauty of a defining moment in a timeless form.',
    image: 'product-images/product-4.jpg',
    fallback: createProductPlaceholder('Eternal First Look', '#211d3a', '#c793ff'),
  },
  {
    id: 5,
    name: 'Black Devil with a Bright Smile',
    price: 10000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.8,
    description: 'A lively midnight refreshment with a bright citrus sparkle and smooth, feel-good finish.',
    image: createProductPlaceholder('Black Devil', '#47311d', '#f2b24a'),
  },
  {
    id: 6,
    name: 'Velvet Ember Glow',
    price: 5000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.9,
    description: 'A rich, smooth blend crafted for late-night rituals and elevated evening moments.',
    image: 'product-images/product-6.jpg',
    fallback: createProductPlaceholder('Velvet Ember', '#2d1b1d', '#b46d5d'),
  },
  {
    id: 7,
    name: 'Midnight Velvet Tray',
    price: 10000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.7,
    description: 'A cozy, elevated refreshment experience designed for relaxed evenings and warm escapes.',
    image: 'product-images/product-7.jpg',
    fallback: createProductPlaceholder('Midnight Velvet', '#291a2e', '#d889a1'),
  },
  {
    id: 8,
    name: 'The Midnight Special',
    price: 1000,
    tag: 'Refreshments',
    category: 'Refreshments',
    rating: 4.9,
    description: 'A crisp, mood-lifting favorite for a fresh reset and a refined after-dark unwind.',
    image: 'product-images/product-8.jpg',
    fallback: createProductPlaceholder('Midnight Special', '#122c2d', '#77d7c5'),
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

function getProductById(productId) {
  return products.find((product) => product.id === productId);
}

function renderProducts() {
  productGrid.innerHTML = products
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-image">
            <img src="${product.image}" alt="${product.name}" onerror="this.onerror=null;this.src='${product.fallback}'" />
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

  const shipping = subtotal > 150 || subtotal === 0 ? 0 : 12;
  const total = subtotal + shipping;

  subtotalEl.textContent = `TZS ${subtotal.toLocaleString()}`;
  shippingEl.textContent = `TZS ${shipping.toLocaleString()}`;
  totalEl.textContent = `TZS ${total.toLocaleString()}`;
}

const cartButton = document.getElementById('cartToggleButton');
const closeCart = document.querySelector('.close-cart');
const checkoutModalBackdrop = document.getElementById('checkoutModalBackdrop');
const checkoutForm = document.getElementById('checkoutForm');
const checkoutTotal = document.getElementById('checkoutTotal');
const closeCheckoutButton = document.querySelector('.close-checkout');

function calculateCartTotals() {
  const subtotal = cart.reduce((total, item) => {
    const product = getProductById(item.id);
    return total + product.price * item.quantity;
  }, 0);

  const shipping = subtotal > 150 || subtotal === 0 ? 0 : 12;
  return { subtotal, shipping, total: subtotal + shipping };
}

function openCheckoutModal() {
  if (!cart.length) {
    alert('Your cart is empty. Add a few favorites first.');
    return;
  }

  const totals = calculateCartTotals();
  checkoutTotal.textContent = `TZS ${totals.total.toLocaleString()}`;
  checkoutModalBackdrop.classList.add('open');
  checkoutModalBackdrop.setAttribute('aria-hidden', 'false');
}

function closeCheckoutModal() {
  checkoutModalBackdrop.classList.remove('open');
  checkoutModalBackdrop.setAttribute('aria-hidden', 'true');
  checkoutForm.reset();
}

cartButton.addEventListener('click', () => {
  cartPanel.classList.add('open');
});

closeCart.addEventListener('click', () => {
  cartPanel.classList.remove('open');
});

closeCheckoutButton.addEventListener('click', closeCheckoutModal);
checkoutModalBackdrop.addEventListener('click', (event) => {
  if (event.target === checkoutModalBackdrop) {
    closeCheckoutModal();
  }
});

document.querySelector('.checkout-btn').addEventListener('click', openCheckoutModal);

checkoutForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(checkoutForm);
  const fullName = formData.get('fullName')?.toString().trim();
  const email = formData.get('email')?.toString().trim();
  const address = formData.get('address')?.toString().trim();
  const city = formData.get('city')?.toString().trim();
  const postalCode = formData.get('postalCode')?.toString().trim();
  const phone = formData.get('phone')?.toString().trim();
  const location = formData.get('location')?.toString().trim();

  if (!fullName || !email || !address || !city || !postalCode || !phone || !location) {
    alert('Please complete your full delivery details, phone number, and exact location before placing the order.');
    return;
  }

  if (!cart.length) {
    alert('Your cart is empty. Add a few favorites before checking out.');
    return;
  }

  try {
    const response = await fetch('http://127.0.0.1:5000/api/orders', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: cart.map((item) => {
          const product = getProductById(item.id);
          return {
            id: item.id,
            name: product.name,
            price: product.price,
            quantity: item.quantity,
          };
        }),
        shippingName: fullName,
        shippingEmail: email,
        shippingAddress: address,
        shippingCity: city,
        shippingPostalCode: postalCode,
        shippingPhone: phone,
        shippingLocation: location,
        paymentMethod: 'cash_on_delivery',
      }),
    });

    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(body.error || 'Order could not be submitted.');
    }

    const totals = calculateCartTotals();
    alert(`Thank you, ${fullName}! Your order for TZS ${totals.total.toLocaleString()} has been placed successfully. Please pay cash on delivery at ${location}. A confirmation email will be sent to ${email}.`);

    cart.length = 0;
    renderCart();
    closeCheckoutModal();
    cartPanel.classList.remove('open');
  } catch (error) {
    alert(error.message || 'An error occurred while placing the order.');
  }
});

renderProducts();
renderCart();
