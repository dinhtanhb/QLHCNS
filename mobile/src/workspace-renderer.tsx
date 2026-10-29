import { useState } from 'react';
import { View } from 'react-native';
import type * as DocumentPicker from 'expo-document-picker';
import { Button, Card, Confirm, Copy, ErrorNote, moneyLabel, s } from './ui';
import { NativeControl } from './workspace-controls';
import type { WorkspaceAction, WorkspaceBlock, WorkspaceField, WorkspaceForm, WorkspacePayload } from './workspace-types';
import { validateWorkspaceField } from './workspace-validation';
import { changeWorkspaceValue } from './workspace-values';

export type PickedUpload = { name: string; file: DocumentPicker.DocumentPickerAsset };
export type WorkspaceActions = { busy: boolean; navigate: (path: string, external?: boolean) => void;
  submit: (payload: WorkspacePayload, files?: PickedUpload[]) => Promise<void> };

function initialValue(field: WorkspaceField) {
  return field.numericLocale && typeof field.value === 'string' ? moneyLabel(field.value) : field.value;
}

function Form({ form, actions }: { form: WorkspaceForm; actions: WorkspaceActions }) {
  const [fields, setFields] = useState(form.fields);
  const [values, setValues] = useState<Record<string, string | string[]>>(() => Object.fromEntries(form.fields.map(field => [field.id, initialValue(field)])));
  const [checks, setChecks] = useState<Record<string, boolean>>(() => Object.fromEntries(form.fields.map(field => [field.id, field.checked])));
  const [files, setFiles] = useState<Record<string, DocumentPicker.DocumentPickerAsset[]>>({});
  const [confirm, setConfirm] = useState<WorkspaceAction | null>(null); const [error, setError] = useState('');
  const [repeatCount, setRepeatCount] = useState(1);
  const submit = async (action: WorkspaceAction) => {
    setError('');
    try {
      const pairs: string[][] = []; const uploads: PickedUpload[] = [];
      for (const field of fields) {
        if (field.disabled) continue;
        if (['checkbox', 'radio'].includes(field.type)) {
          if (field.required && !fields.some(other => other.name === field.name && checks[other.id])) throw new Error('Vui lòng chọn '+field.label+'.');
          if (!checks[field.id]) continue;
        }
        if (field.type === 'file') {
          validateWorkspaceField(field, '', false, files[field.id]?.length || 0);
          for (const file of files[field.id] || []) uploads.push({ name: field.name, file }); continue;
        }
        let value = values[field.id] ?? field.value;
        if (field.numericLocale && typeof value === 'string') {
          const raw = value.trim().replace(/\s/g, '');
          if (raw && !/^[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/.test(raw)) throw new Error(field.label+': nhập số theo dạng 1.000 hoặc 0,5.');
          value = raw.replace(/\./g, '').replace(',', '.');
        }
        validateWorkspaceField(field, value, !!checks[field.id], 0);
        for (const item of Array.isArray(value) ? value : [value]) pairs.push([field.name, item]);
      }
      if (action.name) pairs.push([action.name, action.value]);
      const payload: WorkspacePayload = { path: action.path, method: action.method, fields: pairs, ...(action.print ? { print: true } : {}) };
      if (form.format === 'json') { payload.json = Object.fromEntries(pairs); payload.fields = []; }
      await actions.submit(payload, uploads);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chưa lưu được biểu mẫu.'); }
    finally { setConfirm(null); }
  };
  const add = (prefix: string, template: WorkspaceField[]) => {
    const total = fields.find(field => field.name === prefix+'-TOTAL_FORMS');
    if (!total) return;
    const index = Number(values[total.id] || 0);
    const maximum = fields.find(field => field.name === prefix+'-MAX_NUM_FORMS');
    const limit = maximum ? Number(values[maximum.id] || 1000) : 1000;
    if (index >= Math.min(limit || 1000, 1000)) { setError('Đã đủ số dòng của biểu mẫu.'); return; }
    const added = template.map(field => ({ ...field, id: `${prefix}-${index}-${field.id}`, name: field.name.replace('__prefix__', String(index)) }));
    setFields(previous => [...previous, ...added]);
    setValues(previous => ({ ...previous, [total.id]: String(index+1), ...Object.fromEntries(added.map(field => [field.id, initialValue(field)])) }));
    setChecks(previous => ({ ...previous, ...Object.fromEntries(added.map(field => [field.id, field.checked])) }));
  };
  const remove = (prefix: string, index: number) => {
    const total = fields.find(field => field.name === prefix+'-TOTAL_FORMS');
    const initial = fields.find(field => field.name === prefix+'-INITIAL_FORMS');
    if (!total) return;
    const rowPrefix = `${prefix}-${index}-`;
    const deletion = fields.find(field => field.name === rowPrefix+'DELETE');
    if (deletion) { setChecks(previous => ({ ...previous, [deletion.id]: true })); return; }
    const dropped = fields.filter(field => field.name.startsWith(rowPrefix));
    const remaining = fields.filter(field => !dropped.includes(field)).map(field => {
      if (!field.name.startsWith(prefix+'-')) return field;
      const suffix = field.name.slice(prefix.length+1).match(/^(\d+)-(.*)$/);
      return suffix && Number(suffix[1]) > index ? { ...field, name: `${prefix}-${Number(suffix[1])-1}-${suffix[2]}` } : field;
    });
    setFields(remaining);
    setValues(previous => ({ ...previous, [total.id]: String(Number(previous[total.id] || 0)-1),
      ...(initial && index < Number(previous[initial.id] || 0) ? { [initial.id]: String(Number(previous[initial.id])-1) } : {}) }));
    setFiles(previous => Object.fromEntries(Object.entries(previous).filter(([key]) => !dropped.some(field => field.id === key))));
  };
  return <View testID={'workspace-form-'+form.id}><Card>
    <Blocks blocks={form.blocks} actions={actions} />
    {fields.map(field => {
      const row = field.name.match(/-(\d+)-[^-]+$/);
      const sameName = fields.filter(other => other.name === field.name && other.type !== 'hidden');
      const repeated = sameName.length > 1 && !['radio', 'checkbox', 'hidden'].includes(field.type);
      const display = row && field.type !== 'hidden' ? { ...field, label: `Dòng ${Number(row[1])+1} · ${field.label}` }
        : repeated ? { ...field, label: `Dòng ${sameName.indexOf(field)+1} · ${field.label}` } : field;
      const prefix = Object.keys(form.templates).find(prefix => field.name.startsWith(prefix+'-'));
      const last = prefix && row && !fields.slice(fields.indexOf(field)+1).some(other => other.name.startsWith(`${prefix}-${row[1]}-`) && other.type !== 'hidden');
      return <View key={field.id} style={s.stack}><NativeControl field={display}
        value={values[field.id] ?? field.value} checked={checks[field.id] ?? field.checked} files={files[field.id] || []} busy={actions.busy}
        onChange={value => setValues(previous => changeWorkspaceValue(form, fields, previous, field, value))}
        onFiles={value => setFiles(previous => ({ ...previous, [field.id]: value }))}
        onCheck={checked => setChecks(previous => ({ ...previous,
          ...(field.type === 'radio' ? Object.fromEntries(fields.filter(other => other.name === field.name).map(other => [other.id, false])) : {}), [field.id]: checked }))} />
        {last && prefix && row && field.type !== 'hidden' ? <Button label={`Xóa dòng ${Number(row[1])+1}`} secondary disabled={actions.busy} onPress={() => remove(prefix, Number(row[1]))} /> : null}
      </View>;
    })}
    {Object.entries(form.templates).map(([prefix, template]) => <Button key={prefix} label="Thêm dòng" secondary disabled={actions.busy} onPress={() => add(prefix, template)} />)}
    {form.repeat?.length ? <Button label="Thêm dòng hàng hóa" secondary disabled={actions.busy || repeatCount >= 100} onPress={() => {
      const added = form.repeat!.map(field => ({ ...field, id: `repeat-${repeatCount}-${field.id}` }));
      setFields(previous => [...previous, ...added]);
      setValues(previous => ({ ...previous, ...Object.fromEntries(added.map(field => [field.id, initialValue(field)])) }));
      setRepeatCount(value => value+1);
    }} /> : null}
    <ErrorNote message={error} />
    {form.actions.map((action, index) => <Button key={index} label={action.label} secondary={index > 0 || action.method === 'GET'} busy={actions.busy} onPress={() => {
      if (action.confirm) setConfirm(action); else void submit(action);
    }} />)}
    {confirm ? <Confirm title="Xác nhận thao tác" detail={confirm.confirm} busy={actions.busy} onCancel={() => setConfirm(null)} onConfirm={() => void submit(confirm)} /> : null}
  </Card></View>;
}

export function Blocks({ blocks, actions }: { blocks: WorkspaceBlock[]; actions: WorkspaceActions }) {
  return <View style={s.stack}>{blocks.map((block, index) => {
    if (block.kind === 'text') return <Copy key={index}>{block.text}</Copy>;
    if (block.kind === 'heading') return <Copy key={index} title>{block.text}</Copy>;
    if (block.kind === 'notice') return <ErrorNote key={index} message={block.text} />;
    if (block.kind === 'link') return <Button key={index} label={block.label} secondary disabled={actions.busy} onPress={() => actions.navigate(block.path, block.external)} />;
    if (block.kind === 'print') return <Button key={index} label={block.label} secondary busy={actions.busy} onPress={() => { void actions.submit({ path: block.path, method: 'GET', print: true }).catch(() => undefined); }} />;
    if (block.kind === 'form') return <Form key={index} form={block} actions={actions} />;
    if (block.kind === 'table') return <View key={index} style={s.stack}>{block.rows.map((row, number) => <Card key={number}>
      {row.cells.map((cell, cellIndex) => cell.text ? <View key={cellIndex} style={s.stack}>{cell.label ? <Copy muted>{cell.label}</Copy> : null}<Copy>{cell.text}</Copy></View> : null)}
      <Blocks blocks={row.blocks} actions={actions} />
    </Card>)}</View>;
    return null;
  })}</View>;
}

const isRecord = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);

export function JSONResults({ data, actions }: { data: unknown; actions: WorkspaceActions }) {
  if (!isRecord(data)) return <Copy>Đã xử lý yêu cầu.</Copy>;
  if (Array.isArray(data.turns)) return <View style={s.stack}>{data.turns.map((turn, index) => isRecord(turn) ? <Card key={index}>
    <Copy title>{String(turn.question || 'Tìm tài liệu')}</Copy><JSONResults data={turn.answer} actions={actions} />
  </Card> : null)}{!data.turns.length ? <Copy>Chưa có lịch sử tìm kiếm.</Copy> : null}</View>;
  if (Array.isArray(data.results)) return <View style={s.stack}>
    {data.query ? <Copy title>{String(data.query)}</Copy> : null}
    {data.partial ? <Copy muted>Một phần nguồn tài liệu chưa sẵn sàng. Các kết quả bên dưới vẫn thuộc quyền của bạn.</Copy> : null}
    {data.results.map((row, index) => isRecord(row) ? <Card key={index}><Copy title>{String(row.title || row.text || 'Tài liệu')}</Copy>
      {row.date ? <Copy muted>{String(row.date)}</Copy> : null}{row.snippet ? <Copy>{String(row.snippet)}</Copy> : null}
      {typeof row.url === 'string' ? <Button label="Mở tài liệu" secondary onPress={() => actions.navigate(String(row.url))} /> : null}
      {typeof row.download_url === 'string' ? <Button label="Tải tài liệu" secondary onPress={() => actions.navigate(String(row.download_url))} /> : null}
    </Card> : null)}
    {!data.results.length ? <Copy>Không có kết quả phù hợp trong phạm vi quyền của bạn.</Copy> : null}
    <Button label="Tìm tài liệu khác" secondary onPress={() => actions.navigate('/assistant/')} />
  </View>;
  return <Copy>Đã xử lý yêu cầu.</Copy>;
}
