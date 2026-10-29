import { useEffect, useMemo, useState } from 'react';
import { Modal, Platform, Pressable, ScrollView, Text, View } from 'react-native';
import DateTimePicker, { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import * as DocumentPicker from 'expo-document-picker';
import { Button, Card, Copy, Field, s } from './ui';
import { useTheme } from './theme';
import type { WorkspaceField, WorkspaceJSON } from './workspace-types';
import { useAppearance } from './appearance';
import { useSession } from './session';

const pad = (value: number) => String(value).padStart(2, '0');
const dateValue = (value: Date, type: string) => {
  const date = `${value.getFullYear()}-${pad(value.getMonth()+1)}-${pad(value.getDate())}`;
  if (type === 'month') return date.slice(0, 7);
  if (type === 'time') return `${pad(value.getHours())}:${pad(value.getMinutes())}`;
  return type === 'datetime-local' ? `${date}T${pad(value.getHours())}:${pad(value.getMinutes())}` : date;
};

export function NativeControl({ field, value, checked, files, busy, onChange, onCheck, onFiles }: {
  field: WorkspaceField; value: string | string[]; checked: boolean; files: DocumentPicker.DocumentPickerAsset[]; busy: boolean;
  onChange: (value: string | string[]) => void; onCheck: (checked: boolean) => void;
  onFiles: (files: DocumentPicker.DocumentPickerAsset[]) => void;
}) {
  const t = useTheme(); const [choosing, setChoosing] = useState(false); const [search, setSearch] = useState('');
  const { dark } = useAppearance();
  const { request } = useSession();
  const [dateOpen, setDateOpen] = useState(false); const [fileError, setFileError] = useState('');
  const [remoteOptions, setRemoteOptions] = useState<WorkspaceField['options']>([]); const [queryBusy, setQueryBusy] = useState(false);
  const [remotePage, setRemotePage] = useState(1); const [more, setMore] = useState(false);
  useEffect(() => {
    if (!choosing || !field.remote) return;
    let active = true;
    const timer = setTimeout(() => {
      setQueryBusy(true); setFileError('');
      void request<WorkspaceJSON>('workspace/', { path: `${field.remote}&term=${encodeURIComponent(search)}&page=${remotePage}`, method: 'GET' }).then(result => {
        const data = result.data;
        if (!active || !data || typeof data !== 'object' || !('results' in data) || !Array.isArray(data.results)) return;
        const found: WorkspaceField['options'] = [];
        for (const row of data.results) if (row && typeof row === 'object' && 'id' in row && 'text' in row) found.push({ value: String(row.id), label: String(row.text), disabled: false, selected: false });
        setRemoteOptions(previous => remotePage === 1 ? found : [...previous, ...found]);
        setMore('pagination' in data && !!data.pagination && typeof data.pagination === 'object' && 'more' in data.pagination && data.pagination.more === true);
      }).catch(() => { if (active) setFileError('Chưa tải được lựa chọn. Vui lòng thử lại.'); }).finally(() => { if (active) setQueryBusy(false); });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [choosing, field.remote, remotePage, request, search]);
  const choices = useMemo(() => {
    const all = [...field.options, ...remoteOptions];
    return all.filter((option, index) => all.findIndex(row => row.value === option.value) === index);
  }, [field.options, remoteOptions]);
  const options = useMemo(() => choices.filter(option => option.label.toLocaleLowerCase().includes(search.toLocaleLowerCase())), [choices, search]);
  if (field.type === 'hidden') return null;
  const label = field.label + (field.required ? ' *' : '');
  const disabled = busy || field.disabled || field.readonly;
  if (field.type === 'checkbox' || field.type === 'radio') return <Pressable accessibilityRole={field.type === 'radio' ? 'radio' : 'checkbox'}
    accessibilityLabel={label} accessibilityState={{ checked, disabled }} aria-checked={checked} disabled={disabled}
    {...(Platform.OS === 'web' ? { onKeyDown: (event: unknown) => {
      if (!disabled && event && typeof event === 'object' && 'key' in event && (event.key === ' ' || event.key === 'Enter') && 'preventDefault' in event && typeof event.preventDefault === 'function') {
        event.preventDefault(); onCheck(field.type === 'radio' ? true : !checked);
      }
    } } : {})}
    onPress={() => onCheck(field.type === 'radio' ? true : !checked)}
    style={[s.button, { flexDirection: 'row', justifyContent: 'flex-start', gap: 12, borderColor: checked ? t.brand : t.border, backgroundColor: t.surface }]}>
    <Text style={[s.body, { color: t.text }]}>{checked ? '✓ ' : '○ '}{label}</Text>
  </Pressable>;
  if (field.type === 'select') {
    const selected = Array.isArray(value) ? value : [value];
    const text = choices.filter(option => selected.includes(option.value)).map(option => option.label).join(', ');
    return <View style={s.stack}><Copy>{label}</Copy><Button label={text || 'Chọn '+field.label} secondary disabled={disabled} onPress={() => { setSearch(''); setRemotePage(1); setChoosing(true); }} />
      <Modal visible={choosing} transparent onRequestClose={() => setChoosing(false)}>
        <View style={[s.overlay, { backgroundColor: t.bg }]}><View style={{ flexShrink: 1 }}><Card><Copy title>{field.label}</Copy>
          <Field label={'Tìm '+field.label} value={search} onChangeText={value => { setSearch(value); setRemotePage(1); }} autoCapitalize="none" />
          <ScrollView keyboardShouldPersistTaps="handled" style={{ maxHeight: 400 }} contentContainerStyle={s.stack}>
            {options.map((option, index) => <Button key={index} label={`${selected.includes(option.value) ? '✓ ' : ''}${option.label || '(Trống)'}`} secondary disabled={option.disabled}
              onPress={() => { onChange(field.multiple ? selected.includes(option.value) ? selected.filter(item => item !== option.value) : [...selected, option.value] : option.value); if (!field.multiple) setChoosing(false); }} />)}
            {options.length === 0 && !queryBusy ? <Copy>Không có lựa chọn phù hợp.</Copy> : null}
            {queryBusy ? <Copy>Đang tải lựa chọn…</Copy> : null}{fileError ? <Copy>{fileError}</Copy> : null}
            {more ? <Button label="Tải thêm lựa chọn" secondary busy={queryBusy} onPress={() => setRemotePage(value => value+1)} /> : null}
          </ScrollView><Button label="Xong" secondary onPress={() => setChoosing(false)} />
        </Card></View></View>
      </Modal></View>;
  }
  if (field.type === 'file') return <View style={s.stack}><Copy>{label}</Copy>
    <Button label={'Chọn tệp: '+field.label} secondary disabled={disabled} onPress={() => {
      setFileError('');
      void DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true, multiple: field.multiple }).then(result => {
        if (result.canceled) return;
        if (result.assets.some(file => (file.size || 0) > 20*1024*1024)) { setFileError('Mỗi tệp tối đa 20 MB.'); return; }
        onFiles(result.assets);
      }).catch(() => setFileError('Chưa chọn được tệp. Vui lòng thử lại.'));
    }} />{files.map((file, index) => <Copy key={index}>{file.name}</Copy>)}
    {files.length ? <Button label={'Bỏ tệp: '+field.label} secondary disabled={busy} onPress={() => onFiles([])} /> : null}
    {fileError ? <Copy>{fileError}</Copy> : null}</View>;
  const raw = Array.isArray(value) ? value.join(', ') : value;
  const isDate = ['date', 'month', 'time', 'datetime-local'].includes(field.type);
  const parsed = field.type === 'time' ? new Date(`2000-01-01T${raw || '12:00'}`) : new Date(raw.length === 7 ? raw+'-01T12:00' : raw.length === 10 ? raw+'T12:00' : raw);
  const initialDate = Number.isNaN(parsed.getTime()) ? new Date() : parsed;
  const pick = () => {
    if (Platform.OS !== 'android') { setDateOpen(true); return; }
    DateTimePickerAndroid.open({ value: initialDate, mode: field.type === 'time' ? 'time' : 'date',
      onChange: (event, picked) => {
        if (event.type !== 'set' || !picked) return;
        if (field.type === 'datetime-local') DateTimePickerAndroid.open({ value: picked, mode: 'time', onChange: (next, time) => {
          if (next.type === 'set' && time) { picked.setHours(time.getHours(), time.getMinutes()); onChange(dateValue(picked, field.type)); }
        } });
        else onChange(dateValue(picked, field.type));
      } });
  };
  return <View style={s.stack}><Field label={label} value={raw} onChangeText={onChange} editable={!disabled}
    secureTextEntry={field.type === 'password'} autoCapitalize={['email', 'password', 'url'].includes(field.type) ? 'none' : 'sentences'}
    autoCorrect={field.type === 'password' ? false : undefined} multiline={field.type === 'textarea'}
    keyboardType={field.type === 'number' ? 'decimal-pad' : field.type === 'email' ? 'email-address' : field.type === 'tel' ? 'phone-pad' : 'default'}
    maxLength={field.maxLength || undefined} placeholder={field.placeholder || (field.numericLocale ? 'Ví dụ: 1.000 hoặc 0,5' : isDate ? field.type === 'time' ? 'HH:MM' : field.type === 'month' ? 'YYYY-MM' : field.type === 'datetime-local' ? 'YYYY-MM-DDTHH:MM' : 'YYYY-MM-DD' : undefined)} />
    {isDate && Platform.OS !== 'web' ? <Button label={'Chọn ngày/giờ: '+field.label} secondary disabled={disabled} onPress={pick} /> : null}
    {dateOpen && Platform.OS === 'ios' ? <><DateTimePicker value={initialDate} mode={field.type === 'time' ? 'time' : field.type === 'datetime-local' ? 'datetime' : 'date'}
      themeVariant={dark ? 'dark' : 'light'} onChange={(_, picked) => { if (picked) onChange(dateValue(picked, field.type)); }} />
      <Button label="Xong" secondary onPress={() => setDateOpen(false)} /></> : null}
  </View>;
}
