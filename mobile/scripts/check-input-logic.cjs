// Execute the production TypeScript helpers without React Native or a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const file = path.join(__dirname, '../src/input-utils.ts');
const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const helperExports = {};
vm.runInNewContext(code, { exports: helperExports, Date });
const { normalizeSearch, parseTime, timeLabel, approvalNeedsDetails } = helperExports;
let count = 0;
for (const [query, label] of [['cham cong', 'Chấm công'], ['dang ky', 'Đăng ký'],
  ['bang cong', 'Bảng công'], ['ChẤm CÔng', 'Chấm công'], ['  ĐĂNG KÝ  ', 'đăng ký']]) {
  assert.ok(normalizeSearch(label).includes(normalizeSearch(query)));
  count++;
}
assert.equal(normalizeSearch('chấm'), normalizeSearch('cha\u0302\u0301m'));
count++;
for (const value of ['00:00', '09:30', '12:00', '23:59']) {
  const date = parseTime(value);
  assert.ok(date instanceof Date && Number.isFinite(date.getTime()));
  assert.equal(date.getHours(), Number(value.slice(0, 2)));
  assert.equal(date.getMinutes(), Number(value.slice(3)));
  assert.equal(timeLabel(value), value);
  count++;
}
for (const value of ['', '24:00', '09:60', '9:30', '09:3', 'abc', '2026-10-30', '-1:00']) {
  assert.equal(parseTime(value), null);
  assert.equal(timeLabel(value), 'Chọn giờ');
  count++;
}
for (const [name, reason, scale, expected] of [
  ['QA An', 'Việc gia đình.', 1, false],
  ['Tên dài '.repeat(10), '', 1, true],
  ['QA An', 'Lý do dài '.repeat(20), 1, true],
  ['QA An', 'a\nb\nc\nd', 1, true],
  ['QA An', 'a'.repeat(50), 2, true],
]) {
  assert.equal(approvalNeedsDetails(name, reason, scale), expected);
  count++;
}
console.log(`${count} production helper cases passed; no native picker exercised`);
