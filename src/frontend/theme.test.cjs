const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/js/theme.js'), 'utf8');

function fixture(saved, blocked = false) {
    const listeners = {};
    const attributes = {};
    const button = {
        setAttribute: (key, value) => { attributes[key] = value; },
        getAttribute: key => attributes[key],
        addEventListener: (event, fn) => { listeners[event] = fn; },
    };
    const root = { dataset: {}, style: {} };
    const writes = [];
    const context = {
        document: {
            documentElement: root,
            querySelectorAll: () => [button],
            querySelector: () => null,
            addEventListener: (event, fn) => { listeners[event] = fn; },
        },
        window: { addEventListener: (event, fn) => { listeners[event] = fn; } },
        localStorage: {
            getItem: () => { if (blocked) throw Error('denied'); return saved; },
            setItem: (key, value) => { if (blocked) throw Error('denied'); writes.push([key, value]); },
        },
    };
    vm.runInNewContext(source, context);
    return { root, listeners, attributes, writes, button };
}

test('saved dark mode applies immediately, then accessible toggle saves light', () => {
    const f = fixture('dark');
    assert.equal(f.root.dataset.theme, 'dark');
    assert.equal(f.root.style.colorScheme, 'dark');
    f.listeners.DOMContentLoaded();
    assert.equal(f.attributes['aria-pressed'], 'true');
    f.listeners.click();
    assert.equal(f.root.dataset.theme, 'light');
    assert.equal(f.attributes['aria-pressed'], 'false');
    assert.match(f.attributes['aria-label'], /tối/);
    assert.deepEqual(f.writes, [['ihrms-theme', 'light']]);
});

test('blocked storage still permits toggling without exceptions', () => {
    const f = fixture(null, true);
    assert.equal(f.root.dataset.theme, 'light');
    f.listeners.DOMContentLoaded();
    f.listeners.click();
    assert.equal(f.root.dataset.theme, 'dark');
});

test('invalid preferences and cross-tab deletion safely restore light', () => {
    const f = fixture('untrusted');
    assert.equal(f.root.dataset.theme, 'light');
    f.listeners.DOMContentLoaded();
    f.listeners.storage({ key: 'another-key', newValue: 'dark' });
    assert.equal(f.root.dataset.theme, 'light');
    f.listeners.storage({ key: 'ihrms-theme', newValue: 'dark' });
    assert.equal(f.root.dataset.theme, 'dark');
    f.listeners.storage({ key: 'ihrms-theme', newValue: null });
    assert.equal(f.root.dataset.theme, 'light');
});
