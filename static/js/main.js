// 次元漫谈 - 前端交互脚本

document.addEventListener('DOMContentLoaded', function () {

  // ==================== 导航栏汉堡菜单 ====================
  const navToggle = document.querySelector('.navbar-toggle');
  const navMenu = document.querySelector('.navbar-nav');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', function () {
      navMenu.classList.toggle('open');
    });

    // 点击外部关闭菜单
    document.addEventListener('click', function (e) {
      if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove('open');
      }
    });
  }

  // ==================== Flash 消息自动关闭 ====================
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    // 5秒后自动消失
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(function () {
        if (alert.parentNode) {
          alert.parentNode.removeChild(alert);
        }
      }, 500);
    }, 5000);

    // 关闭按钮
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        alert.style.opacity = '0';
        setTimeout(function () {
          if (alert.parentNode) alert.parentNode.removeChild(alert);
        }, 300);
      });
    }
  });

  // ==================== 删除确认模态框 ====================
  const modal = document.getElementById('confirm-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');
  const modalConfirm = document.getElementById('modal-confirm');
  const modalCancel = document.getElementById('modal-cancel');

  let pendingForm = null;

  // 绑定所有需要确认的删除按钮
  document.querySelectorAll('[data-confirm]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const confirmMsg = btn.getAttribute('data-confirm') || '确认执行此操作？';
      const title = btn.getAttribute('data-title') || '确认操作';

      if (modalTitle) modalTitle.textContent = title;
      if (modalBody) modalBody.textContent = confirmMsg;

      // 找到最近的 form 或者自身 form
      pendingForm = btn.closest('form');
      if (!pendingForm && btn.getAttribute('data-form-id')) {
        pendingForm = document.getElementById(btn.getAttribute('data-form-id'));
      }

      if (modal) modal.classList.add('active');
    });
  });

  if (modalConfirm) {
    modalConfirm.addEventListener('click', function () {
      if (pendingForm) {
        pendingForm.submit();
      }
      if (modal) modal.classList.remove('active');
    });
  }

  if (modalCancel) {
    modalCancel.addEventListener('click', function () {
      if (modal) modal.classList.remove('active');
      pendingForm = null;
    });
  }

  if (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        modal.classList.remove('active');
        pendingForm = null;
      }
    });
  }

  // ==================== 字符计数器 ====================
  document.querySelectorAll('[data-maxlength]').forEach(function (el) {
    const max = parseInt(el.getAttribute('data-maxlength'));
    const counterId = el.getAttribute('data-counter');
    const counter = counterId ? document.getElementById(counterId) : null;

    function updateCounter() {
      const len = el.value.length;
      if (counter) {
        counter.textContent = len + ' / ' + max;
        if (len > max * 0.9) {
          counter.style.color = 'var(--warning)';
        } else {
          counter.style.color = 'var(--text-muted)';
        }
      }
    }

    el.addEventListener('input', updateCounter);
    updateCounter();
  });

  // ==================== 活跃导航链接高亮 ====================
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav a').forEach(function (link) {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    }
  });

  // ==================== 管理员侧边栏高亮 ====================
  document.querySelectorAll('.admin-nav-link').forEach(function (link) {
    const href = link.getAttribute('href');
    if (href && window.location.pathname === href) {
      link.classList.add('active');
    }
  });

  // ==================== 搜索框回车提交 ====================
  const searchInput = document.querySelector('.search-input input');
  if (searchInput) {
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        const form = searchInput.closest('form');
        if (form) form.submit();
      }
    });
  }

  // ==================== 回复框 Ctrl+Enter 提交 ====================
  document.querySelectorAll('textarea').forEach(function (ta) {
    ta.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = ta.closest('form');
        if (form) form.submit();
      }
    });
  });

  // ==================== 表格中的编辑分类内联表单 ====================
  document.querySelectorAll('.edit-category-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const rowId = btn.getAttribute('data-row');
      const viewRow = document.getElementById('view-row-' + rowId);
      const editRow = document.getElementById('edit-row-' + rowId);
      if (viewRow) viewRow.style.display = 'none';
      if (editRow) editRow.style.display = 'table-row';
    });
  });

  document.querySelectorAll('.cancel-edit-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const rowId = btn.getAttribute('data-row');
      const viewRow = document.getElementById('view-row-' + rowId);
      const editRow = document.getElementById('edit-row-' + rowId);
      if (viewRow) viewRow.style.display = 'table-row';
      if (editRow) editRow.style.display = 'none';
    });
  });

  // ==================== 平滑滚动到回复区域 ====================
  if (window.location.hash === '#replies') {
    const repliesSection = document.getElementById('replies');
    if (repliesSection) {
      setTimeout(function () {
        repliesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }

  // ==================== 图片加载错误处理 ====================
  document.querySelectorAll('img.user-avatar').forEach(function (img) {
    img.addEventListener('error', function () {
      img.style.display = 'none';
      const placeholder = img.nextElementSibling;
      if (placeholder && placeholder.classList.contains('avatar-placeholder-fallback')) {
        placeholder.style.display = 'flex';
      }
    });
  });

  console.log('🌸 次元漫谈 - 前端脚本加载完成');
});
