/* Login only: a second tab/login rotates Django's CSRF cookie. Keep an old
 * login form in sync without resubmitting credentials or weakening server checks. */
(() => {
    'use strict';
    const form = document.querySelector('form[data-login-csrf]');
    if (!form) return;
    function syncToken() {
        const field = form.querySelector('input[name="csrfmiddlewaretoken"]');
        const cookie = document.cookie.split(';').map(part => part.trim())
            .find(part => part.startsWith('csrftoken='));
        if (!field || !cookie) return;
        const token = cookie.slice('csrftoken='.length);
        // Django accepts the current unmasked 32-character cookie secret.
        // Missing/malformed cookies retain the server-rendered token and fail closed.
        if (/^[A-Za-z0-9]{32}$/.test(token)) field.value = token;
    }
    window.addEventListener('pageshow', syncToken);
    form.addEventListener('submit', syncToken);
})();
