/* Locale display proxies preserve native number validation and canonical POST values. */
(() => {
 'use strict';
 const sources = new WeakMap();
 function format(raw) {
  if (!/^[+-]?\d+(?:\.\d+)?$/.test(raw)) return raw;
  const [whole, fraction] = raw.split('.');
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (fraction ? ',' + fraction : '');
 }
 function parse(text) {
  const raw = text.trim().replace(/\s/g, '');
  if (!raw) return '';
  if (!/^[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/.test(raw)) return null;
  return raw.replace(/\./g, '').replace(',', '.');
 }
 function enhance(input) {
  if (sources.has(input) || input.closest('.hcns-paper') || !input.form || input.dataset.uiNumber === 'plain' || /(?:^|[_-])(?:year|month|day)(?:$|[_-])/.test(input.name) || /(?:^|[_-])year(?:$|[_-])/.test(input.id)) return;
  const proxy = document.createElement('input');
  proxy.type = 'text'; proxy.inputMode = 'decimal';
  proxy.className = input.className + ' ui-number-display';
  proxy.id = input.id ? input.id + '-display' : '';
  for (const attr of ['aria-label','aria-describedby','placeholder','title','form']) {
   if (input.hasAttribute(attr)) proxy.setAttribute(attr, input.getAttribute(attr));
  }
  proxy.disabled = input.disabled; proxy.readOnly = input.readOnly;
  proxy.required = input.required;
  const label = input.id && document.querySelector('label[for="'+CSS.escape(input.id)+'"]');
  if (label) label.htmlFor = proxy.id;
  if (!label && !proxy.hasAttribute('aria-label')) proxy.setAttribute('aria-label', input.getAttribute('aria-label') || input.name.replace(/[_-]/g,' '));
  proxy.value = format(input.value); input.after(proxy);
  input.classList.add('ui-number-source'); input.tabIndex = -1; input.setAttribute('aria-hidden','true');
  sources.set(input, proxy);
  const sync = () => {
   const canonical = parse(proxy.value);
   proxy.setCustomValidity(canonical === null ? 'Nhập số theo dạng 5.000.000 hoặc 0,07.' : '');
   input.value = canonical === null ? '' : canonical;
   proxy.setAttribute('aria-invalid', String(canonical === null || !input.validity.valid));
   return canonical !== null;
  };
  proxy.addEventListener('input', () => { sync(); input.dispatchEvent(new Event('input',{bubbles:true})); });
  proxy.addEventListener('change', () => { sync(); input.dispatchEvent(new Event('change',{bubbles:true})); });
  proxy.addEventListener('blur', () => { if (sync()) proxy.value = format(input.value); });
  input.addEventListener('invalid', event => { event.preventDefault(); proxy.setCustomValidity(input.validationMessage); proxy.focus(); proxy.reportValidity(); });
  input.addEventListener('input', () => { if (document.activeElement !== proxy) proxy.value = format(input.value); });
  input.form.addEventListener('reset', () => setTimeout(() => { proxy.value = format(input.value); proxy.setCustomValidity(''); },0));
 }
 const scan = () => document.querySelectorAll('main input[type=number], .content-wrapper input[type=number]').forEach(enhance);
 scan();
 new MutationObserver(scan).observe(document.querySelector('main, .content-wrapper') || document.body,{childList:true,subtree:true});
 window.IhrmsNumbers = {format, parse, refresh: () => { scan(); document.querySelectorAll('main input[type=number], .content-wrapper input[type=number]').forEach(input => { const proxy=sources.get(input); if(proxy && document.activeElement!==proxy) proxy.value=format(input.value); }); }};
})();
