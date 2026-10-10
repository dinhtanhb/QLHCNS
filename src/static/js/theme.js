/* Only a display preference is persisted; no account or business data. */
(function () {
    'use strict';
    const root = document.documentElement;
    const key = 'ihrms-theme';
    function apply(mode) {
        root.dataset.theme = mode === 'dark' ? 'dark' : 'light';
        root.style.colorScheme = root.dataset.theme;
        document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
            const dark = root.dataset.theme === 'dark';
            button.setAttribute('aria-pressed', String(dark));
            button.setAttribute('aria-label', dark ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối');
            button.textContent = dark ? '☀' : '☾';
            button.title = button.getAttribute('aria-label');
        });
    }
    let saved = 'light';
    try { saved = localStorage.getItem(key) || 'light'; } catch (_) { /* Storage may be disabled. */ }
    apply(saved);
    document.addEventListener('DOMContentLoaded', function () {
        const adminNav = document.querySelector('#jazzy-navbar .navbar-nav');
        if (adminNav && !document.querySelector('[data-theme-toggle]')) {
            const item = document.createElement('li');
            item.className = 'nav-item';
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'ihrms-theme-toggle';
            button.setAttribute('data-theme-toggle', '');
            item.appendChild(button);
            adminNav.appendChild(item);
        }
        apply(root.dataset.theme);
        document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
            button.addEventListener('click', function () {
                const mode = root.dataset.theme === 'dark' ? 'light' : 'dark';
                apply(mode);
                try { localStorage.setItem(key, mode); } catch (_) { /* The toggle still works. */ }
            });
        });
    });
    window.addEventListener('storage', function (event) {
        if (event.key === key) apply(event.newValue || 'light');
    });
}());
