const lampToggle = document.getElementById('lampToggle');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const modeButtons = document.querySelectorAll('.mode-btn');
const loginEmailInput = document.getElementById('loginEmail');
const loginPasswordInput = document.getElementById('loginPassword');
const registerEmailInput = document.getElementById('registerEmail');
const registerPasswordInput = document.getElementById('registerPassword');
const togglePasswordButton = document.querySelector('.toggle-password');
const toggleRegisterPasswordButton = document.querySelector('.toggle-register-password');
const loginError = document.getElementById('loginError');
const registerError = document.getElementById('registerError');
const verificationList = document.getElementById('verificationList');
const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
let verifiedCustomer = false;

function getApiBase() {
  if (window.location.protocol === 'file:') {
    return 'http://127.0.0.1:5000';
  }
  return window.location.origin || 'http://127.0.0.1:5000';
}

async function checkCustomerSession() {
  try {
    const result = await fetchJson('/api/customer/status');
    if (result.loggedIn) {
      window.location.href = 'index.html';
    }
  } catch (error) {
    // Not logged in yet; allow page to load.
  }
}

function showMessage(element, message, type) {
  if (!element) return;
  element.textContent = message;
  element.classList.remove('error', 'success');
  element.classList.add(type, 'visible');
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

async function fetchJson(url, options = {}) {
  const fullUrl = `${getApiBase()}${url}`;
  const response = await fetch(fullUrl, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.error || 'Request failed.');
  }

  return body;
}

function renderVerificationList() {
  if (!verificationList) return;

  fetch(`${API_BASE}/api/users/pending`)
    .then((response) => response.json())
    .then((users) => {
      if (!Array.isArray(users) || !users.length) {
        verificationList.innerHTML = '<div class="empty-state">No pending requests.</div>';
        return;
      }

      verificationList.innerHTML = users
        .map(
          (user) => `
            <div class="verification-item">
              <div class="meta">
                <strong>${user.email}</strong>
                <span class="verification-code">Code: ${user.verificationCode}</span>
              </div>
              <button type="button" class="verify-btn" data-email="${user.email}">Verify</button>
            </div>
          `
        )
        .join('');

      verificationList.querySelectorAll('.verify-btn').forEach((button) => {
        button.addEventListener('click', async () => {
          const email = button.dataset.email;

          try {
            const result = await fetchJson('/api/verify', {
              method: 'POST',
              body: JSON.stringify({ email }),
            });

            renderVerificationList();
            showMessage(registerError, result.message || `${email} has been approved and can now log in.`, 'success');
          } catch (error) {
            showMessage(registerError, error.message, 'error');
          }
        });
      });
    })
    .catch(() => {
      verificationList.innerHTML = '<div class="empty-state">No pending requests.</div>';
    });
}

function setMode(mode) {
  const isLogin = mode === 'login';
  loginForm.classList.toggle('active', isLogin);
  registerForm.classList.toggle('active', !isLogin);

  modeButtons.forEach((button) => {
    const active = button.dataset.mode === mode;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

modeButtons.forEach((button) => {
  button.addEventListener('click', () => setMode(button.dataset.mode));
});

lampToggle.addEventListener('click', () => {
  const isOn = document.body.classList.toggle('lamp-on');
  lampToggle.setAttribute('aria-pressed', String(isOn));
  lampToggle.querySelector('.lamp-label').textContent = isOn ? 'Lamp on' : 'Turn on lamp';

  if (!isOn) {
    loginError.classList.remove('visible', 'error', 'success');
    registerError.classList.remove('visible', 'error', 'success');
    loginError.textContent = '';
    registerError.textContent = '';
    return;
  }

  setMode(verifiedCustomer ? 'login' : 'register');
});

togglePasswordButton?.addEventListener('click', () => {
  const isPassword = loginPasswordInput.type === 'password';
  loginPasswordInput.type = isPassword ? 'text' : 'password';
  togglePasswordButton.textContent = isPassword ? 'Hide' : 'Show';
  togglePasswordButton.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
});

toggleRegisterPasswordButton?.addEventListener('click', () => {
  const isPassword = registerPasswordInput.type === 'password';
  registerPasswordInput.type = isPassword ? 'text' : 'password';
  toggleRegisterPasswordButton.textContent = isPassword ? 'Hide' : 'Show';
  toggleRegisterPasswordButton.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
});

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const email = loginEmailInput.value.trim();
  const password = loginPasswordInput.value.trim();

  if (!document.body.classList.contains('lamp-on')) {
    showMessage(loginError, 'Turn on the lamp first to unlock the login form.', 'error');
    return;
  }

  if (!email || !password) {
    showMessage(loginError, 'Please enter both your email and password.', 'error');
    return;
  }

  if (!validateEmail(email)) {
    showMessage(loginError, 'Please enter a valid email address.', 'error');
    return;
  }

  try {
    const result = await fetchJson('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    showMessage(loginError, result.message || 'Secure login successful. Redirecting...', 'success');
    loginForm.reset();

    window.setTimeout(() => {
      window.location.href = 'index.html';
    }, 1200);
  } catch (error) {
    showMessage(loginError, error.message, 'error');
  }
});

registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const email = registerEmailInput.value.trim();
  const password = registerPasswordInput.value.trim();

  if (!document.body.classList.contains('lamp-on')) {
    showMessage(registerError, 'Turn on the lamp first to continue registration.', 'error');
    return;
  }

  if (!email || !password) {
    showMessage(registerError, 'Please enter both email and password.', 'error');
    return;
  }

  if (!validateEmail(email)) {
    showMessage(registerError, 'Please enter a valid email address.', 'error');
    return;
  }

  if (password.length < 8) {
    showMessage(registerError, 'Use a password with at least 8 characters.', 'error');
    return;
  }

  try {
    const result = await fetchJson('/api/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    verifiedCustomer = false;
    document.body.classList.remove('lamp-on');
    lampToggle.setAttribute('aria-pressed', 'false');
    lampToggle.querySelector('.lamp-label').textContent = 'Turn on lamp';
    renderVerificationList();
    showMessage(registerError, result.message || `Verification code sent to ${email}. Owner approval is required before login.`, 'success');
    registerForm.reset();
    setMode('register');
  } catch (error) {
    showMessage(registerError, error.message, 'error');
  }
});

renderVerificationList();
setMode('register');
checkCustomerSession();
