import type { WorkspaceField } from './workspace-types';

function compareDecimal(left: string, right: string) {
  const parts = (value: string) => {
    const negative = value.startsWith('-');
    const [whole, fraction = ''] = value.replace(/^[+-]/, '').split('.');
    return { negative, whole: whole.replace(/^0+(?=\d)/, ''), fraction };
  };
  const a = parts(left), b = parts(right);
  if (a.negative !== b.negative) return a.negative ? -1 : 1;
  const direction = a.negative ? -1 : 1;
  if (a.whole.length !== b.whole.length) return direction*(a.whole.length > b.whole.length ? 1 : -1);
  if (a.whole !== b.whole) return direction*(a.whole > b.whole ? 1 : -1);
  const length = Math.max(a.fraction.length, b.fraction.length);
  const af = a.fraction.padEnd(length, '0'), bf = b.fraction.padEnd(length, '0');
  return af === bf ? 0 : direction*(af > bf ? 1 : -1);
}

export function validateWorkspaceField(field: WorkspaceField, value: string | string[], checked: boolean, fileCount: number) {
  const raw = Array.isArray(value) ? value.join('') : value;
  if (field.required && (field.type === 'file' ? !fileCount : field.type === 'checkbox' ? !checked : !raw))
    throw new Error('Vui lòng nhập '+field.label+'.');
  if (!raw || field.type === 'file' || field.type === 'hidden') return;
  if (field.maxLength && raw.length > field.maxLength) throw new Error(field.label+': nội dung quá dài.');
  if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw)) throw new Error(field.label+': email chưa hợp lệ.');
  if (field.type === 'number') {
    if (!/^[+-]?\d+(?:\.\d+)?$/.test(raw)) throw new Error(field.label+': số chưa hợp lệ.');
    if (field.min && compareDecimal(raw, field.min) < 0) throw new Error(field.label+': giá trị phải từ '+field.min+'.');
    if (field.max && compareDecimal(raw, field.max) > 0) throw new Error(field.label+': giá trị không quá '+field.max+'.');
  }
  if (['date', 'month', 'datetime-local', 'time'].includes(field.type)) {
    const expression = field.type === 'date' ? /^\d{4}-\d{2}-\d{2}$/ : field.type === 'month' ? /^\d{4}-\d{2}$/ : field.type === 'time' ? /^\d{2}:\d{2}(?::\d{2})?$/ : /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$/;
    if (!expression.test(raw)) throw new Error(field.label+': ngày hoặc giờ chưa đúng định dạng.');
    if (field.min && raw < field.min) throw new Error(field.label+': thời điểm phải từ '+field.min+'.');
    if (field.max && raw > field.max) throw new Error(field.label+': thời điểm không quá '+field.max+'.');
  }
}
