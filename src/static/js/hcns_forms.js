(() => {
  'use strict';
  const form = document.getElementById('hcns-draft-form');
  let changed = false;
  form?.addEventListener('input', () => { changed = true; });
  form?.addEventListener('change', () => { changed = true; });
  const referenceElement = document.getElementById('hcns-reference-data');
  const references = referenceElement ? JSON.parse(referenceElement.textContent) : {};
  const setField = (scope, key, value) => {
    const input = scope === form ? form.elements[key] : scope.querySelector(`[name$="-${key}"]`);
    if (input) input.value = value ?? '';
  };
  form?.addEventListener('change', event => {
    const select = event.target;
    const pool = select.dataset.reference, key = select.dataset.referenceKey;
    if (!pool) return;
    const row = select.closest('tr');
    const data = references[pool]?.[select.value] || {};
    if (row && ['name','code','candidate','candidate_code'].includes(key)) {
      const slots = pool === 'assets' ? ['name','code','type','brand','quantity','condition','location','serial','funding','purchase_date','unit','value']
        : pool === 'candidates' ? ['candidate','candidate_code'] : ['position'];
      slots.forEach(slot => setField(row, slot, data[slot]));
    } else if (!row && key === 'full_name') {
      const slots = pool === 'employees'
        ? ['position','department','new_position','manager','manager_position','date_of_birth','national_id','tax_code','insurance_no','phone','email','address','gender','birth_year','join_date','leave_date']
        : ['phone','email','address','gender','birth_year'];
      slots.forEach(slot => setField(form, slot, data[slot]));
      ['salary','salary_words','salary_note','contract_no','contract_date','effective_date','from_date','to_date',
       'account_name','account_number','bank','bank_branch','id_issue_date','id_issue_place','nationality','qualification','home_phone'].forEach(slot => setField(form, slot, ''));
    } else if (!row && ['recipient','manager'].includes(key)) {
      setField(form, `${key}_position`, data.position);
    }
  });
  const salary = form?.elements.salary;
  const salaryWords = form?.elements.salary_words;
  if (salary && salaryWords) {
    const digits = ['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín'];
    const units = ['','nghìn','triệu','tỷ','nghìn tỷ'];
    const updateWords = () => {
      let amount = Number(salary.value);
      if (!salary.value || !Number.isInteger(amount) || amount < 0 || amount > 9999999999999) { salaryWords.value = ''; return; }
      if (amount === 0) { salaryWords.value = 'Không đồng chẵn'; return; }
      const groups = [], words = [];
      while (amount) { groups.push(amount % 1000); amount = Math.floor(amount / 1000); }
      for (let index = groups.length - 1; index >= 0; index--) {
        const group = groups[index];
        if (!group) continue;
        const hundreds = Math.floor(group / 100), tens = Math.floor((group % 100) / 10), ones = group % 10;
        if (hundreds || words.length) words.push(digits[hundreds], 'trăm');
        if (tens) words.push(tens === 1 ? 'mười' : digits[tens] + ' mươi');
        else if (ones && (hundreds || words.length)) words.push('linh');
        if (ones) words.push(ones === 1 && tens > 1 ? 'mốt' : ones === 5 && tens ? 'lăm' : digits[ones]);
        if (units[index]) words.push(units[index]);
      }
      const text = words.join(' ') + ' đồng chẵn';
      salaryWords.value = text.charAt(0).toUpperCase() + text.slice(1);
    };
    salary.addEventListener('input', updateWords);
    updateWords();
  }
  const exportName = document.getElementById('hcns-export-name')?.dataset.filename;
  const pageTitle = document.title;
  window.addEventListener('beforeprint', () => { if (exportName) document.title = exportName; });
  window.addEventListener('afterprint', () => { document.title = pageTitle; });
  document.getElementById('hcns-print')?.addEventListener('click', () => {
    if (changed) {
      alert('Nội dung vừa thay đổi. Hãy bấm Cập nhật bản xem trước rồi in để lấy đúng nội dung mới.');
      return;
    }
    window.print();
  });
  document.querySelectorAll('.hcns-table-editor').forEach(editor => {
    const prefix = editor.dataset.prefix;
    const body = editor.querySelector('tbody');
    const total = editor.querySelector(`[name="${prefix}-TOTAL_FORMS"]`);
    const renumber = () => {
      Array.from(body.rows).forEach((row, i) => {
        row.querySelectorAll('input,select,textarea').forEach(input => {
          input.name = input.name.replace(new RegExp(`^${prefix}-\\d+-`), `${prefix}-${i}-`);
          input.id = input.id.replace(new RegExp(`^id_${prefix}-\\d+-`), `id_${prefix}-${i}-`);
        });
      });
      total.value = body.rows.length;
      changed = true;
    };
    editor.querySelector('.hcns-add')?.addEventListener('click', () => {
      if (body.rows.length >= Number(editor.dataset.maxRows)) {
        alert(`Tối đa ${editor.dataset.maxRows} dòng cho một bản soạn thảo.`);
        return;
      }
      const fragment = editor.querySelector('template').content.cloneNode(true);
      fragment.querySelectorAll('input,select,textarea').forEach(input => {
        input.name = input.name.replace('__prefix__', String(body.rows.length));
        input.id = input.id.replace('__prefix__', String(body.rows.length));
      });
      body.appendChild(fragment);
      renumber();
    });
    body.addEventListener('click', event => {
      if (event.target.classList.contains('hcns-remove')) {
        event.target.closest('tr').remove();
        renumber();
      }
    });
  });
})();
