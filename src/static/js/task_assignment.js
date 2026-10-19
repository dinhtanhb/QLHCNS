/* Task assignment only. Native controls and server validation also work without JS. */
(() => {
 'use strict';
 const codes = document.getElementById('task_create-act_code');
 const name = document.getElementById('task_create-task_name');
 const data = document.getElementById('task-code-names');
 if (!codes || !name || !data) return;
 const names = JSON.parse(data.textContent);
 let administrativeName = codes.value === '__OTHER__' ? name.value : '';
 function updateName() {
  const other = codes.value === '__OTHER__';
  name.readOnly = !other;
  name.required = other;
  name.value = other ? administrativeName : (names[codes.value] || '');
 }
 name.addEventListener('input', () => { if (codes.value === '__OTHER__') administrativeName = name.value; });
 codes.addEventListener('change', updateName);
 updateName();
})();
