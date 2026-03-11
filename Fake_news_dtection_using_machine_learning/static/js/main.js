/**
 * InfoTrust — Main JavaScript
 */

// ── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 5000) {
  const container = document.querySelector('.toast-container');
  if (!container) return;

  const icons  = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
  const titles = { success: 'Success', error: 'Error', warning: 'Warning', info: 'Information' };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i class="fas ${icons[type] || icons.info}"></i></div>
    <div class="toast-content">
      <div class="toast-title">${titles[type] || titles.info}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
  `;
  container.appendChild(toast);
  setTimeout(() => { toast.style.animation = 'slideInRight 0.3s ease-out reverse'; setTimeout(() => toast.remove(), 300); }, duration);
}

// Convert Django messages to toasts on load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.django-messages .alert').forEach(msg => {
    let type = 'info';
    if (msg.classList.contains('alert-success')) type = 'success';
    else if (msg.classList.contains('alert-danger')) type = 'error';
    else if (msg.classList.contains('alert-warning')) type = 'warning';
    showToast(msg.textContent.trim(), type);
    msg.remove();
  });
});

// ── Loading Overlay ───────────────────────────────────────────────────────
function showLoading() {
  let overlay = document.getElementById('loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
  }
  overlay.style.display = 'flex';
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'none';
}

// ── CSRF / AJAX ───────────────────────────────────────────────────────────
function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? decodeURIComponent(cookie.trim().split('=')[1]) : '';
}

async function ajax(url, options = {}) {
  const config = {
    method: 'GET',
    headers: { 'X-CSRFToken': getCSRFToken(), 'X-Requested-With': 'XMLHttpRequest' },
    ...options,
  };
  if (options.body && typeof options.body === 'object') {
    config.headers['Content-Type'] = 'application/json';
    config.body = JSON.stringify(options.body);
  }
  const response = await fetch(url, config);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const ct = response.headers.get('content-type');
  return ct && ct.includes('application/json') ? response.json() : response.text();
}

// ── Debounce ──────────────────────────────────────────────────────────────
function debounce(fn, wait = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

// ── Smooth scroll for hash links ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });
});

// ── Active nav highlighting ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
      link.classList.add('active');
    }
  });
});

// ── Navbar shadow on scroll ───────────────────────────────────────────────
window.addEventListener('scroll', () => {
  const navbar = document.querySelector('.navbar');
  if (navbar) navbar.style.boxShadow = window.scrollY > 20
    ? '0 2px 12px rgba(15,45,107,0.12)'
    : '0 1px 0 var(--border)';
}, { passive: true });

// ── Global export ─────────────────────────────────────────────────────────
window.InfoTrust = { showToast, showLoading, hideLoading, ajax, getCSRFToken, debounce };
