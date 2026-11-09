const $ = (s, r = document) => r.querySelector(s);

/* toast */
let t;
function toast(msg){
  const el = $('#toast');
  el.textContent = msg; el.classList.add('show');
  clearTimeout(t); t = setTimeout(() => el.classList.remove('show'), 2800);
}

/* mobile menu */
const header = $('#header'), toggle = $('#menuToggle');
toggle.addEventListener('click', () => {
  const open = header.classList.toggle('open');
  toggle.setAttribute('aria-expanded', open);
  toggle.textContent = open ? '✕' : '☰';
});
document.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => {
  header.classList.remove('open'); toggle.textContent = '☰';
}));

/* date picker: shows "Select date" until chosen */
const date = $('#date');
const today = new Date().toISOString().split('T')[0];
date.addEventListener('click', () => {
  date.readOnly = false; date.type = 'date'; date.min = today;
  try { date.showPicker(); } catch (e) {}
});
date.addEventListener('blur', () => {
  if (!date.value) { date.type = 'text'; date.readOnly = true; }
});
date.addEventListener('change', () => {
  if (date.value) {
    const d = new Date(date.value + 'T00:00:00');
    date.dataset.iso = date.value;
  }
});

/* search */
$('#search').addEventListener('submit', e => {
  e.preventDefault();
  const from = $('#from').value.trim(), to = $('#to').value.trim();
  if (!date.value) return toast('Please select a journey date.');
  if (from.toLowerCase() === to.toLowerCase()) return toast('Departure and destination cannot be the same.');
  const pax = $('#pax').selectedOptions[0].text;
  toast(`Searching rides: ${from} → ${to} on ${date.value} (${pax})`);
  // TODO: fetch(`/api/rides?from=${from}&to=${to}&date=${date.value}&pax=${$('#pax').value}`)
});

/* placeholder actions – connect to your routes */
const labels = {login:'Login', register:'Register', publish:'Publish a Ride', heritage:'Our Heritage', explore:'Explore Tamil Nadu', help:'Help'};
document.querySelectorAll('[data-action]').forEach(el => el.addEventListener('click', e => {
  e.preventDefault();
  toast(`${labels[el.dataset.action]} page – connect your route here`);
}));
