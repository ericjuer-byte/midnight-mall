const accessForm = document.getElementById('accessForm');
const visitorNameInput = document.getElementById('visitorName');
const visitorEmailInput = document.getElementById('visitorEmail');
const accessTypeInput = document.getElementById('accessType');
const accessMessage = document.getElementById('accessMessage');

function showAccessMessage(message, isError = false) {
  accessMessage.textContent = message;
  accessMessage.style.color = isError ? '#ff8a8a' : '#8df0c1';
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

accessForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const fullName = visitorNameInput.value.trim();
  const email = visitorEmailInput.value.trim();
  const accessType = accessTypeInput.value;

  if (!fullName || !email) {
    showAccessMessage('Please enter your name and email.', true);
    return;
  }

  if (!validateEmail(email)) {
    showAccessMessage('Please provide a valid email address.', true);
    return;
  }

  const accessSummary = `${fullName} (${accessType})`;
  showAccessMessage(`Welcome, ${accessSummary}. Redirecting to the mall...`);

  const guest = {
    name: fullName,
    email,
    accessType,
    enteredAt: new Date().toISOString(),
  };

  localStorage.setItem('beforeMidnightMallGuest', JSON.stringify(guest));

  window.setTimeout(() => {
    window.location.href = 'index.html';
  }, 900);
});
