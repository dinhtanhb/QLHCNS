/* Only a display preference is persisted; no account or business data. */
(function () {
    'use strict';
    const root = document.documentElement;
    const paletteMeta = document.querySelector('meta[name="ui-palette"]');
    if (paletteMeta) root.dataset.palette = paletteMeta.content;
    const key = 'ihrms-theme';
    const preference = window.matchMedia('(prefers-color-scheme: dark)');
    let selected = null;
    function systemMode() { return preference.matches ? 'dark' : 'light'; }
    function apply(mode) {
        root.dataset.theme = mode === 'dark' ? 'dark' : 'light';
        root.style.colorScheme = root.dataset.theme;
        const themeMeta = document.querySelector('meta[name="theme-color"]');
        if (themeMeta) {
            const background = getComputedStyle(root).getPropertyValue('--ui-bg').trim();
            if (background) themeMeta.content = background;
        }
        document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
            const dark = root.dataset.theme === 'dark';
            button.setAttribute('aria-pressed', String(dark));
            button.setAttribute('aria-label', dark ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối');
            const path = dark ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2"/>' : '<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>';
            // Only constant, decorative SVG markup; no user-controlled HTML.
            button.innerHTML = '<svg class="ui-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
            button.title = button.getAttribute('aria-label');
        });
    }
    try {
        const saved = localStorage.getItem(key);
        selected = saved === 'dark' || saved === 'light' ? saved : null;
    } catch (_) { /* Storage may be disabled. */ }
    apply(selected || systemMode());
    preference.addEventListener('change', function () { if (!selected) apply(systemMode()); });
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
                selected = mode;
                apply(mode);
                try { localStorage.setItem(key, mode); } catch (_) { /* The toggle still works. */ }
            });
        });
    });
    window.addEventListener('storage', function (event) {
        if (event.key === key || event.key === null) {
            selected = event.newValue === 'light' || event.newValue === 'dark' ? event.newValue : null;
            apply(selected || systemMode());
        }
    });
}());
