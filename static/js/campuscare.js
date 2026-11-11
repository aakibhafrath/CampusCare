/* CampusCare - Main JavaScript */

document.addEventListener('DOMContentLoaded', function () {

  // ─── Sidebar Toggle ───────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    sidebar && sidebar.classList.add('show');
    overlay && overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar && sidebar.classList.remove('show');
    overlay && overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  sidebarToggle && sidebarToggle.addEventListener('click', openSidebar);
  sidebarClose && sidebarClose.addEventListener('click', closeSidebar);
  overlay && overlay.addEventListener('click', closeSidebar);

  // ─── Active nav item highlight ─────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ─── Auto-dismiss alerts ───────────────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.alert.fade.show').forEach(alert => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert && bsAlert.close();
    });
  }, 5000);

  // ─── Confirm dialogs on data-confirm elements ──────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
        return false;
      }
    });
  });

  // ─── AJAX mark notification as read ───────────────────────
  document.querySelectorAll('.mark-read-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const url = this.href;
      const item = this.closest('.notification-item');

      fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'ok') {
            item && item.classList.remove('unread');
            this.style.display = 'none';
            updateNotifBadge();
          }
        })
        .catch(() => { window.location.href = url; });
    });
  });

  // ─── Live notification badge update ───────────────────────
  function updateNotifBadge() {
    fetch('/notifications/api/count/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(r => r.json())
      .then(data => {
        const badges = document.querySelectorAll('.notif-badge');
        badges.forEach(badge => {
          if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = '';
          } else {
            badge.style.display = 'none';
          }
        });
      });
  }

  // ─── Form validation feedback ──────────────────────────────
  const forms = document.querySelectorAll('.needs-validation');
  forms.forEach(form => {
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  // ─── Tooltip initialization ────────────────────────────────
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(el => new bootstrap.Tooltip(el));

});

