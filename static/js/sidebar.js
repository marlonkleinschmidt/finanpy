const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');

function setSidebarOpen(open) {
  sidebar.classList.toggle('invisible', !open);
  sidebar.classList.toggle('-translate-x-full', !open);
  sidebarOverlay.classList.toggle('hidden', !open);
  sidebarToggle.setAttribute('aria-expanded', String(open));
}

sidebarToggle.addEventListener('click', () => {
  setSidebarOpen(sidebarToggle.getAttribute('aria-expanded') !== 'true');
});
sidebarOverlay.addEventListener('click', () => setSidebarOpen(false));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    setSidebarOpen(false);
  }
});
