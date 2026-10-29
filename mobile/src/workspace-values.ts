import type { WorkspaceField, WorkspaceForm } from './workspace-types';
import { moneyLabel } from './ui';

export function changeWorkspaceValue(form: WorkspaceForm, fields: WorkspaceField[], previous: Record<string, string | string[]>, field: WorkspaceField, value: string | string[]) {
  const result = { ...previous, [field.id]: value };
  if (field.name === 'task_name') result.__administrative_name = value;
  if (!field.reference || !field.referenceKey || typeof value !== 'string') return result;
  const data = form.references?.[field.reference]?.[value] || {};
  if (field.reference === 'task_codes' || field.reference === 'activity_codes') {
    const name = field.reference === 'task_codes' ? 'task_name' : 'activity_name';
    const target = fields.find(other => other.name === name);
    if (target) result[target.id] = field.reference === 'task_codes' && value === '__OTHER__'
      ? previous.__administrative_name || '' : String(data[name] ?? (value ? previous[target.id] || '' : ''));
    return result;
  }
  const row = field.name.match(/^(.*-\d+-)[^-]+$/)?.[1] || '';
  let slots: string[] = [];
  let clear: string[] = [];
  if (row && ['name', 'code', 'candidate', 'candidate_code'].includes(field.referenceKey)) {
    slots = field.reference === 'assets' ? ['name', 'code', 'type', 'brand', 'quantity', 'condition', 'location', 'serial', 'funding', 'purchase_date', 'unit', 'value']
      : field.reference === 'candidates' ? ['candidate', 'candidate_code'] : ['position'];
  } else if (!row && field.referenceKey === 'full_name') {
    slots = field.reference === 'employees' ? ['position', 'department', 'new_position', 'manager', 'manager_position', 'date_of_birth', 'national_id', 'tax_code', 'insurance_no', 'phone', 'email', 'address', 'gender', 'birth_year', 'join_date', 'leave_date']
      : ['phone', 'email', 'address', 'gender', 'birth_year'];
    clear = ['salary', 'salary_words', 'salary_note', 'contract_no', 'contract_date', 'effective_date', 'from_date', 'to_date', 'account_name', 'account_number', 'bank', 'bank_branch', 'id_issue_date', 'id_issue_place', 'nationality', 'qualification', 'home_phone'];
  } else if (!row && ['recipient', 'manager'].includes(field.referenceKey)) {
    const target = fields.find(other => other.name === field.referenceKey+'_position');
    if (target) result[target.id] = String(data.position ?? '');
  }
  for (const slot of [...slots, ...clear]) {
    const target = fields.find(other => other.name === row+slot);
    if (!target) continue;
    const raw = clear.includes(slot) ? '' : String(data[slot] ?? '');
    result[target.id] = target.numericLocale ? moneyLabel(raw) : raw;
  }
  return result;
}
