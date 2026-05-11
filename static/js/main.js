/* ============================================================
   AI Study Buddy  –  Global JS
   ============================================================ */

// ── Theme ──────────────────────────────────────────────────────
(function () {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function getTheme() { return document.documentElement.getAttribute('data-theme'); }

function toggleTheme() {
  const next = getTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.classList.toggle('dark', next === 'dark');
    btn.title = next === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.classList.toggle('dark', getTheme() === 'dark');
    btn.addEventListener('click', toggleTheme);
  });
});

// ── Toast ──────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  requestAnimationFrame(() => { requestAnimationFrame(() => { t.classList.add('show'); }); });
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ── Fetch helpers ──────────────────────────────────────────────
async function postJSON(url, data) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return r.json();
}

async function deleteJSON(url) {
  const r = await fetch(url, { method: 'DELETE' });
  return r.json();
}

// ── Score ring renderer ────────────────────────────────────────
function renderScoreRing(el, score) {
  const r = 40, circ = 2 * Math.PI * r;
  el.innerHTML = `
    <svg viewBox="0 0 100 100" width="100" height="100">
      <circle class="track" cx="50" cy="50" r="${r}"/>
      <circle class="fill" cx="50" cy="50" r="${r}"
        stroke-dasharray="${circ}"
        stroke-dashoffset="${circ - (score / 100) * circ}"/>
    </svg>
    <div class="label">${score}<span style="font-size:.6rem">%</span></div>
  `;
}
