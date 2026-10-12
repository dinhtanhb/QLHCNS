/* Presentation state only: no account/business data is stored. */
(function () {
    'use strict';
    const body = document.body;
    const sidebar = document.getElementById('portalSidebar');
    const toggle = document.getElementById('mobileNavToggle');
    const close = document.getElementById('drawerClose');
    const overlay = document.getElementById('drawerOverlay');
    const main = document.getElementById('mainWrap');
    const header = document.getElementById('ui-topbar');
    const skipLink = document.querySelector('.ui-skip-link');
    const tooltip = document.getElementById('navTooltip');
    const desktop = window.matchMedia('(min-width: 1024px)');
    const userButton = document.getElementById('userMenuButton');
    const userPanel = document.getElementById('userDropdown');
    const userContainer = document.getElementById('userMenuContainer');
    let drawerOpen = false;
    let previousFocus = null;
    let priorInert = [];
    let tooltipOwner = null;
    let collapsed = false;
    try { collapsed = localStorage.getItem('ihrms-sidebar-collapsed') === 'true'; } catch (_) { /* Optional storage. */ }
    function visibleFocusables(container) {
        return Array.from(container.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]'))
            .filter(el => el.getClientRects().length && !el.closest('[hidden],[inert]'));
    }
    function userOpen(open, restore) {
        if (!userButton || !userPanel) return;
        userPanel.hidden = !open;
        userButton.setAttribute('aria-expanded', String(open));
        if (restore) userButton.focus();
    }
    function hideTooltip() {
        if (!tooltip) return;
        tooltip.hidden = true;
        if (tooltipOwner) tooltipOwner.removeAttribute('aria-describedby');
        tooltipOwner = null;
    }
    function state() {
        body.dataset.sidebarCollapsed = String(collapsed);
        if (!toggle) return;
        toggle.setAttribute('aria-expanded', String(desktop.matches ? !collapsed : drawerOpen));
        toggle.setAttribute('aria-label', desktop.matches ? (collapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng') : (drawerOpen ? 'Đóng điều hướng' : 'Mở điều hướng'));
    }
    function drawer(open, restore = true) {
        if (!sidebar || !toggle || (open && desktop.matches)) return;
        if (drawerOpen === open) return;
        drawerOpen = open;
        sidebar.classList.toggle('is-drawer-open', open);
        overlay.hidden = !open;
        document.documentElement.classList.toggle('ui-drawer-lock', open);
        hideTooltip();
        if (open) {
            userOpen(false);
            previousFocus = toggle;
            priorInert = [header, main, skipLink].map(el => [el, el.inert]);
            priorInert.forEach(([el]) => { el.inert = true; });
            sidebar.setAttribute('role', 'dialog');
            sidebar.setAttribute('aria-modal', 'true');
            sidebar.setAttribute('aria-labelledby', 'drawerTitle');
            close.focus();
        } else {
            priorInert.forEach(([el, inert]) => { el.inert = inert; });
            priorInert = [];
            sidebar.removeAttribute('role');
            sidebar.removeAttribute('aria-modal');
            sidebar.removeAttribute('aria-labelledby');
            if (restore && previousFocus && previousFocus.isConnected) previousFocus.focus();
        }
        state();
    }
    if (header && window.ResizeObserver) {
        new ResizeObserver(() => body.style.setProperty('--ui-shell-header-height', header.getBoundingClientRect().height + 'px')).observe(header);
    }
    if (sidebar) {
        sidebar.querySelectorAll('[data-menu-trigger]').forEach(button => {
            const panel = document.getElementById(button.getAttribute('aria-controls'));
            button.addEventListener('click', () => {
                panel.hidden = !panel.hidden;
                button.setAttribute('aria-expanded', String(!panel.hidden));
            });
        });
        const links = Array.from(sidebar.querySelectorAll('[data-nav-link]'));
        const serverCurrent = new Set(links.filter(link => link.getAttribute('aria-current') === 'page'));
        const current = new URL(window.location.href);
        const matches = links.map(link => {
            const url = new URL(link.href);
            const pathMatches = current.pathname === url.pathname || (url.pathname !== '/portal/' && current.pathname.startsWith(url.pathname.endsWith('/') ? url.pathname : url.pathname + '/'));
            const queryMatches = Array.from(url.searchParams).every(([key, value]) => current.searchParams.get(key) === value) ||
                (current.pathname === url.pathname && serverCurrent.has(link));
            return {link, url, matches: pathMatches && queryMatches, score: url.pathname.length + (url.search ? url.search.length : 0)};
        }).filter(item => item.matches);
        const score = Math.max(0, ...matches.map(item => item.score));
        links.forEach(link => link.removeAttribute('aria-current'));
        matches.filter(item => item.score === score).forEach(({link}) => {
            link.setAttribute('aria-current', 'page');
            const group = link.closest('.ui-nav-group');
            if (group) {
                const button = group.querySelector('[data-menu-trigger]');
                document.getElementById(button.getAttribute('aria-controls')).hidden = false;
                button.setAttribute('aria-expanded', 'true');
                button.classList.add('is-current-group');
            }
        });
        links.forEach(link => link.addEventListener('click', () => { if (!desktop.matches) drawer(false); }));
        function showTooltip(target) {
            const item = target.closest('.ui-nav-link,.ui-nav-trigger');
            if (!item || !sidebar.contains(item) || !desktop.matches || !collapsed) return;
            hideTooltip();
            tooltipOwner = item;
            tooltip.textContent = item.querySelector('.ui-nav-label').textContent.trim();
            tooltip.hidden = false;
            const rect = item.getBoundingClientRect();
            const gap = parseFloat(getComputedStyle(body).fontSize) * parseFloat(getComputedStyle(body).getPropertyValue('--ui-space-3'));
            tooltip.style.left = sidebar.getBoundingClientRect().right + gap + 'px';
            tooltip.style.top = Math.max(gap, Math.min(rect.top, window.innerHeight - tooltip.offsetHeight - gap)) + 'px';
            item.setAttribute('aria-describedby', 'navTooltip');
        }
        sidebar.addEventListener('focusin', event => showTooltip(event.target));
        sidebar.addEventListener('focusout', () => hideTooltip());
        sidebar.addEventListener('mouseover', event => showTooltip(event.target));
        sidebar.addEventListener('mouseleave', event => { if (!tooltip.contains(event.relatedTarget)) hideTooltip(); });
        tooltip.addEventListener('mouseleave', hideTooltip);
        sidebar.addEventListener('scroll', hideTooltip);
        toggle.addEventListener('click', () => {
            if (desktop.matches) {
                collapsed = !collapsed;
                try { localStorage.setItem('ihrms-sidebar-collapsed', String(collapsed)); } catch (_) { /* UI remains functional. */ }
                hideTooltip(); state();
            } else drawer(!drawerOpen);
        });
        close.addEventListener('click', () => drawer(false));
        overlay.addEventListener('click', () => drawer(false));
        desktop.addEventListener('change', () => { drawer(false); hideTooltip(); state(); });
    }
    if (userButton) {
        userButton.addEventListener('click', () => userOpen(userPanel.hidden));
        userContainer.addEventListener('focusout', event => {
            // Chromium runs microtasks between blur and focus. Do not hide a
            // link while a pointer is transferring focus inside this disclosure.
            if (event.relatedTarget) {
                if (!userContainer.contains(event.relatedTarget)) userOpen(false);
                return;
            }
            setTimeout(() => {
                if (!userContainer.contains(document.activeElement)) userOpen(false);
            }, 0);
        });
    }
    document.addEventListener('click', event => {
        if (userContainer && !userContainer.contains(event.target)) userOpen(false);
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            if (drawerOpen) { event.preventDefault(); drawer(false); }
            else if (userPanel && !userPanel.hidden) { event.preventDefault(); userOpen(false, true); }
            hideTooltip();
        }
        if (event.key === 'Tab' && drawerOpen) {
            const elements = visibleFocusables(sidebar);
            const first = elements[0]; const last = elements[elements.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    document.addEventListener('focusin', event => {
        if (drawerOpen && !sidebar.contains(event.target)) close.focus();
    });
    const breadcrumb = document.querySelector('[data-breadcrumb]');
    const heading = document.querySelector('#main-content h1');
    const pageTitle = document.title.replace(/ — IHRMS$/, '').trim();
    const title = pageTitle !== 'Cổng thông tin nhân viên' ? pageTitle : (heading ? heading.textContent.trim() : '');
    if (breadcrumb && title && title !== 'Cổng thông tin nhân viên' && title !== 'Trang chủ') {
        breadcrumb.querySelector('[data-breadcrumb-title]').textContent = title;
        breadcrumb.hidden = false;
    }
    state();
}());
