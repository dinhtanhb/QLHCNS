/* Searchable catalog choices. Native selects remain the submitted source and
   the no-JavaScript fallback; free-text suggestions continue to use datalist. */
(() => {
 'use strict';
 const normalize = text => text.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
 document.querySelectorAll('.ui-field select:not([multiple])').forEach((select, index) => {
  if (select.disabled || select.options.length < 10 || ['month','year','payroll_month','payroll_year'].includes(select.name) || select.closest('.hcns-paper,.hcns-editor')) return;
  const label = select.labels?.[0];
  const input = document.createElement('input');
  input.type = 'text'; input.className = 'ui-choice-search'; input.id = (select.id || 'ui-select-' + index) + '-search';
  input.autocomplete = 'off'; input.spellcheck = false; input.placeholder = 'Nhập để tìm và chọn…'; input.required = select.required;
  input.dataset.uiChoiceSource = select.id;
  input.setAttribute('role', 'combobox'); input.setAttribute('aria-autocomplete', 'list'); input.setAttribute('aria-expanded', 'false');
  if (select.getAttribute('aria-describedby')) input.setAttribute('aria-describedby', select.getAttribute('aria-describedby'));
  const control = document.createElement('div'); control.className = 'ui-select-control ui-combobox';
  const popup = document.createElement('div'); popup.className = 'ui-choice-popover'; popup.id = input.id + '-popup'; popup.setAttribute('popover', 'manual');
  const list = document.createElement('div'); list.id = input.id + '-list'; list.className = 'ui-choice-list'; list.setAttribute('role', 'listbox');
  list.setAttribute('aria-label', label?.textContent.trim() || 'Danh mục'); input.setAttribute('aria-controls', list.id);
  const status = document.createElement('p'); status.className = 'ui-field-help ui-choice-status'; status.setAttribute('role', 'status');
  const toggle = document.createElement('button'); toggle.type = 'button'; toggle.className = 'ui-choice-toggle'; toggle.tabIndex = -1;
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); icon.setAttribute('viewBox','0 0 24 24'); icon.setAttribute('aria-hidden','true'); icon.classList.add('ui-icon');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path'); path.setAttribute('d','m6 9 6 6 6-6'); path.setAttribute('fill','none'); path.setAttribute('stroke','currentColor'); path.setAttribute('stroke-width','2'); icon.append(path); toggle.append(icon);
  toggle.setAttribute('aria-label', 'Mở lựa chọn'); toggle.setAttribute('aria-controls', list.id); toggle.setAttribute('aria-expanded', 'false');
  select.before(control); control.append(input, toggle, select); popup.append(list, status); control.after(popup);
  select.hidden = true; select.required = false; select.tabIndex = -1;
  if (label) label.htmlFor = input.id;
  let matches = [], active = -1, opened = false;
  const initialHidden = new WeakMap([...select.options].map(option => [option, option.hidden]));
  const excluded = option => option.disabled || (option.dataset.uiExcluded === undefined ? initialHidden.get(option) : option.dataset.uiExcluded === 'true');
  const selectedText = () => select.selectedOptions[0]?.value ? select.selectedOptions[0].textContent.trim() : '';
  const validate = () => input.setCustomValidity(input.value === selectedText() && (!select.value || !excluded(select.selectedOptions[0])) ? '' : 'Chọn một giá trị trong danh sách.');
  function position() {
   const r = control.getBoundingClientRect(), gap = 8;
   popup.style.width = Math.min(Math.max(r.width, 320), innerWidth - gap * 2) + 'px';
   const height = Math.min(popup.scrollHeight, 320), below = innerHeight - r.bottom - gap;
   popup.style.maxHeight = Math.max(120, Math.min(320, Math.max(below, r.top - gap))) + 'px';
   popup.style.left = Math.max(gap, Math.min(r.left, innerWidth - popup.offsetWidth - gap)) + 'px';
   popup.style.top = Math.max(gap, below >= height ? r.bottom + gap : r.top - height - gap) + 'px';
  }
  function close(restore = false) {
   if (restore) input.value = selectedText();
   if (opened) popup.hidePopover();
   opened = false; input.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); validate();
  }
  function choose(option) {
   select.value = option.value; input.value = selectedText(); close();
   select.dispatchEvent(new Event('change', {bubbles:true})); input.focus();
  }
  function activate(index) {
   active = Math.max(0, Math.min(index, matches.length - 1));
   [...list.children].forEach((row, i) => { row.dataset.active = String(i === active); });
   const row = list.children[active];
   if (row) { input.setAttribute('aria-activedescendant', row.id); row.scrollIntoView({block:'nearest'}); }
  }
  function render(query = '') {
   const q = normalize(query.trim());
   matches = [...select.options].filter(option => !excluded(option) && (!q || normalize(option.textContent + ' ' + (option.dataset.search || '')).includes(q)));
   list.replaceChildren(); active = -1; input.removeAttribute('aria-activedescendant');
   matches.forEach((option, i) => {
    const row = document.createElement('div'); row.className = 'ui-choice-option'; row.id = list.id + '-' + i; row.setAttribute('role', 'option');
    row.setAttribute('aria-selected', String(option.selected)); row.textContent = option.textContent + (option.dataset.search ? ' — ' + option.dataset.search : '');
    row.addEventListener('mousedown', event => event.preventDefault()); row.addEventListener('click', () => choose(option)); list.append(row);
   });
   status.textContent = matches.length ? '' : 'Không có lựa chọn phù hợp. Thử từ tìm khác.';
   if (opened) position();
  }
  function open(query = '') {
   render(query);
   if (!opened) { popup.showPopover(); opened = true; }
   input.setAttribute('aria-expanded', 'true'); toggle.setAttribute('aria-expanded', 'true'); position();
  }
  input.value = selectedText(); validate();
  input.addEventListener('focus', () => open());
  input.addEventListener('input', () => { open(input.value); validate(); });
  input.addEventListener('blur', () => close());
  input.addEventListener('keydown', event => {
   if (event.key === 'Escape') { event.preventDefault(); close(true); }
   else if (['ArrowDown','ArrowUp'].includes(event.key)) { event.preventDefault(); if (!opened) open(); activate(active < 0 ? (event.key === 'ArrowDown' ? 0 : matches.length - 1) : active + (event.key === 'ArrowDown' ? 1 : -1)); }
   else if (event.key === 'Enter' && opened) { event.preventDefault(); if (matches[active]) choose(matches[active]); }
   else if (event.key === 'Tab') close();
  });
  toggle.addEventListener('mousedown', event => event.preventDefault());
  toggle.addEventListener('click', () => { if (opened) close(true); else { input.focus(); open(); } });
  select.addEventListener('change', () => { input.value = selectedText(); validate(); });
  select.addEventListener('ui:choiceschanged', () => { input.value = selectedText(); render(); validate(); });
  select.form?.addEventListener('reset', () => requestAnimationFrame(() => { input.value = selectedText(); close(); }));
  window.addEventListener('resize', () => close(true));
  document.addEventListener('scroll', () => { if (opened) position(); }, true);
 });
})();
