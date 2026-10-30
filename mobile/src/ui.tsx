import { PropsWithChildren, ReactNode, useCallback, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleProp, StyleSheet, Text, TextInput, TextInputProps, TextStyle, View, ViewStyle } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import DateTimePicker, { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import { useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from './theme';
import { useSession } from './session';
import { radius, space, type } from './tokens';
import type { Page } from './types';

export const s = StyleSheet.create({
  page: { flex: 1 }, content: { padding: space.x4, gap: space.x6, width: '100%', maxWidth: 768, alignSelf: 'center', paddingBottom: space.x8 },
  card: { borderWidth: 1, borderRadius: radius.card, padding: space.x4, gap: space.x3 },
  row: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space.x3 },
  between: { justifyContent: 'space-between' }, stack: { gap: space.x2 }, grow: { flex: 1 },
  heading: { fontSize: type.page, lineHeight: 32, fontWeight: '600' }, title: { fontSize: type.title, lineHeight: 26, fontWeight: '600' },
  body: { fontSize: type.body, lineHeight: 24 }, small: { fontSize: type.label, lineHeight: 20 },
  button: { minHeight: 48, paddingHorizontal: space.x4, paddingVertical: space.x3, borderRadius: radius.control, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  buttonText: { fontSize: type.body, lineHeight: 24, fontWeight: '600', textAlign: 'center' },
  input: { borderWidth: 1, borderRadius: radius.control, paddingHorizontal: space.x3, paddingVertical: space.x3, fontSize: type.body, minHeight: 48 },
  overlay: { flex: 1, justifyContent: 'center', padding: space.x4 },
});

type IconName = React.ComponentProps<typeof Ionicons>['name'];

export function Copy({ children, muted = false, title = false, style }: PropsWithChildren<{ muted?: boolean; title?: boolean; style?: StyleProp<TextStyle> }>) {
  const t = useTheme();
  return <Text style={[title ? s.title : s.body, { color: muted ? t.muted : t.text }, style]}>{children}</Text>;
}

export function IconButton({ label, icon, onPress, disabled = false, size = 20 }: { label: string; icon: IconName; onPress: () => void; disabled?: boolean; size?: number }) {
  const t = useTheme();
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => ({ minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: radius.control,
      backgroundColor: pressed ? t.bg : 'transparent', opacity: disabled ? 0.5 : 1 })}>
    <Ionicons name={icon} size={size} color={t.text} />
  </Pressable>;
}

export function AppBar({ title, onBack, backLabel = 'Quay lại', action, actionLabel }: { title: string; onBack?: () => void; backLabel?: string; action?: ReactNode; actionLabel?: string }) {
  const t = useTheme();
  return <View style={{ minHeight: 56, paddingHorizontal: onBack ? space.x2 : space.x4, flexDirection: 'row', alignItems: 'center', gap: space.x2, backgroundColor: t.bg }}>
    {onBack ? <IconButton label={backLabel} icon="arrow-back" onPress={onBack} /> : null}
    <Text accessibilityRole="header" numberOfLines={2} style={{ flex: 1, flexShrink: 1, color: t.text, fontSize: type.title, lineHeight: 24, fontWeight: '600' }}>{title}</Text>
    {action ? <View accessibilityLabel={actionLabel} style={{ minWidth: 44, alignItems: 'center' }}>{action}</View> : null}
  </View>;
}

export function Screen({ title, description, children, compact = false, scrollable = true, onBack, backLabel, action }: PropsWithChildren<{
  title: string; description?: string; compact?: boolean; scrollable?: boolean; onBack?: () => void; backLabel?: string; action?: ReactNode;
}>) {
  const t = useTheme();
  const content = <>
    {!compact ? <View style={s.stack}><Text accessibilityRole="header" style={[s.heading, { color: t.text }]}>{title}</Text>
      {description ? <Copy muted>{description}</Copy> : null}</View> : null}
    {children}
  </>;
  return <SafeAreaView edges={['top', 'left', 'right']} style={[s.page, { backgroundColor: t.bg }]}>
    {compact ? <AppBar title={title} onBack={onBack} backLabel={backLabel} action={action} /> : null}
    {scrollable ? <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>{content}</ScrollView>
      : <View style={[compact ? { width: '100%', maxWidth: 768, alignSelf: 'center' } : s.content, { flex: 1, minHeight: 0 }]}>{content}</View>}
  </SafeAreaView>;
}

export function Card({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  const t = useTheme(); return <View style={[s.card, { backgroundColor: t.surface, borderColor: t.cardBorder }, style]}>{children}</View>;
}

export function Button({ label, onPress, secondary = false, variant, disabled = false, busy = false, icon, accessibilityLabel, style }: {
  label: string; onPress: () => void; secondary?: boolean; variant?: 'primary' | 'secondary' | 'text'; disabled?: boolean; busy?: boolean; icon?: IconName; accessibilityLabel?: string; style?: StyleProp<ViewStyle>;
}) {
  const t = useTheme(); const level = variant || (secondary ? 'secondary' : 'primary');
  const primary = level === 'primary'; const tertiary = level === 'text';
  return <Pressable accessibilityRole="button" accessibilityLabel={accessibilityLabel || label} accessibilityState={{ disabled: disabled || busy, busy }}
    disabled={disabled || busy} onPress={onPress}
    style={({ pressed }) => [s.button, { flexDirection: 'row', gap: space.x2,
      backgroundColor: primary ? t.brand : tertiary ? 'transparent' : t.surface,
      borderColor: primary ? t.brand : tertiary ? 'transparent' : t.border,
      paddingHorizontal: tertiary ? space.x2 : space.x4,
      opacity: disabled || busy ? 0.55 : pressed ? 0.78 : 1 }, style]}>
    {busy ? <ActivityIndicator color={primary ? t.onBrand : t.brand} accessibilityLabel="Đang xử lý" /> : <>
      {icon ? <Ionicons name={icon} size={18} color={primary ? t.onBrand : tertiary ? t.brand : t.text} /> : null}
      <Text allowFontScaling style={[s.buttonText, { color: primary ? t.onBrand : tertiary ? t.brand : t.text }]}>{label}</Text>
    </>}
  </Pressable>;
}

export function Field({ label, ...props }: TextInputProps & { label: string }) {
  const t = useTheme();
  return <View style={s.stack}><Copy>{label}</Copy><TextInput accessibilityLabel={label} placeholderTextColor={t.muted}
    {...props} style={[s.input, { color: t.text, borderColor: t.border, backgroundColor: t.surface }, props.style]} /></View>;
}

export function ListItem({ title, subtitle, icon, trailing, onPress, accessibilityLabel }: { title: string; subtitle?: string; icon?: IconName; trailing?: ReactNode; onPress?: () => void; accessibilityLabel?: string }) {
  const t = useTheme(); const content = <>
    {icon ? <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: t.bg, alignItems: 'center', justifyContent: 'center' }}><Ionicons name={icon} size={20} color={t.brand} /></View> : null}
    <View style={{ flex: 1, minWidth: 0, gap: 2 }}><Copy title>{title}</Copy>{subtitle ? <Copy muted>{subtitle}</Copy> : null}</View>
    {trailing || (onPress ? <Ionicons name="chevron-forward" size={18} color={t.muted} /> : null)}
  </>;
  return onPress ? <Pressable accessibilityRole="button" accessibilityLabel={accessibilityLabel || title} onPress={onPress}
    style={({ pressed }) => [{ minHeight: 56, padding: space.x3, flexDirection: 'row', alignItems: 'center', gap: space.x3, borderRadius: radius.control, backgroundColor: pressed ? t.bg : t.surface }]}>{content}</Pressable>
    : <View style={{ minHeight: 56, padding: space.x3, flexDirection: 'row', alignItems: 'center', gap: space.x3 }}>{content}</View>;
}

export function SectionHeader({ title, detail, action, icon }: { title: string; detail?: string; action?: ReactNode; icon?: IconName }) {
  const t = useTheme();
  return <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.x2, minHeight: 40 }}>
    {icon ? <Ionicons name={icon} size={20} color={t.brand} /> : null}<View style={{ flex: 1, minWidth: 0 }}><Text accessibilityRole="header" style={{ color: t.text, fontSize: type.section, lineHeight: 26, fontWeight: '600' }}>{title}</Text>
      {detail ? <Copy muted>{detail}</Copy> : null}</View>{action}
  </View>;
}

type StatusTone = 'success' | 'warning' | 'danger' | 'info';
export function StatusChip({ label, tone = 'info', icon }: { label: string; tone?: StatusTone; icon?: IconName }) {
  const t = useTheme(); const colors = tone === 'success' ? [t.success, t.successBg] : tone === 'warning' ? [t.warning, t.warningBg]
    : tone === 'danger' ? [t.danger, t.dangerBg] : [t.info, t.infoBg];
  const iconName = icon || (tone === 'success' ? 'checkmark-circle-outline' : tone === 'warning' ? 'time-outline' : tone === 'danger' ? 'close-circle-outline' : 'information-circle-outline');
  return <View accessibilityRole="text" accessibilityLabel={label} style={{ alignSelf: 'flex-start', minHeight: 28, paddingHorizontal: space.x2,
    borderRadius: radius.pill, flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: colors[1] }}>
    <Ionicons name={iconName} size={14} color={colors[0]} /><Text allowFontScaling style={{ color: colors[0], fontSize: type.label, lineHeight: 20, fontWeight: '600' }}>{label}</Text>
  </View>;
}

export function EmptyState({ icon = 'file-tray-outline', title, description, action }: { icon?: IconName; title: string; description: string; action?: { label: string; onPress: () => void } }) {
  const t = useTheme();
  return <View style={{ minHeight: 176, padding: space.x6, borderRadius: radius.card, backgroundColor: t.surface, alignItems: 'center', justifyContent: 'center', gap: space.x2 }}>
    <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: t.bg, alignItems: 'center', justifyContent: 'center' }}><Ionicons name={icon} size={24} color={t.brand} /></View>
    <Text accessibilityRole="header" style={{ color: t.text, fontSize: type.title, lineHeight: 24, fontWeight: '600', textAlign: 'center' }}>{title}</Text>
    <Copy muted style={{ textAlign: 'center' }}>{description}</Copy>
    {action ? <Button label={action.label} onPress={action.onPress} variant="text" /> : null}
  </View>;
}

export function Skeleton({ lines = 3 }: { lines?: number }) {
  const t = useTheme();
  return <View accessibilityRole="progressbar" accessibilityLabel="Đang tải nội dung" style={[s.stack, { padding: space.x4 }]}>
    {Array.from({ length: lines }, (_, i) => <View key={i} style={{ height: i === 0 ? 20 : 14, width: i === lines-1 ? '62%' : '100%', borderRadius: radius.control, backgroundColor: t.cardBorder }} />)}
  </View>;
}

export type Choice = { value: string; label: string; disabled?: boolean };
export function Chip({ label, selected, onPress, accessibilityRole = 'button' }: { label: string; selected: boolean; onPress: () => void; accessibilityRole?: 'button' | 'radio' }) {
  const t = useTheme();
  return <Pressable accessibilityRole={accessibilityRole} accessibilityLabel={label} accessibilityState={{ selected }} aria-checked={selected} onPress={onPress}
    style={({ pressed }) => ({ minHeight: 44, paddingHorizontal: space.x3, paddingVertical: space.x2, borderRadius: radius.pill,
      alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: selected ? t.brand : t.cardBorder,
      backgroundColor: selected ? t.brand : t.surface, opacity: pressed ? 0.8 : 1 })}>
    <Text allowFontScaling style={{ color: selected ? t.onBrand : t.text, fontSize: type.label, lineHeight: 20, fontWeight: '600' }}>{label}</Text>
  </Pressable>;
}

export function SegmentedControl<T extends string>({ value, options, onChange, label }: { value: T; options: { value: T; label: string }[]; onChange: (value: T) => void; label: string }) {
  const t = useTheme();
  return <View accessibilityRole="radiogroup" accessibilityLabel={label} style={{ flexDirection: 'row', gap: space.x1, padding: space.x1, borderRadius: radius.card, backgroundColor: t.surface }}>
    {options.map(option => <View key={option.value} style={{ flex: 1, minWidth: 0 }}><Chip label={option.label} selected={value === option.value} accessibilityRole="radio" onPress={() => onChange(option.value)} /></View>)}
  </View>;
}

export function SelectSheet({ label, value, options, onChange, disabled = false }: { label: string; value: string; options: Choice[]; onChange: (value: string) => void; disabled?: boolean }) {
  const t = useTheme(); const [open, setOpen] = useState(false); const [search, setSearch] = useState('');
  const shown = options.filter(option => option.label.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
  const selected = options.find(option => option.value === value)?.label;
  return <>
    <View style={s.stack}><Copy>{label}</Copy><Pressable accessibilityRole="button" accessibilityLabel={`${label}: ${selected || 'Chọn'}`} accessibilityState={{ disabled }} disabled={disabled}
      onPress={() => { setSearch(''); setOpen(true); }} style={[s.button, { flexDirection: 'row', justifyContent: 'space-between', gap: space.x2, backgroundColor: t.surface, borderColor: t.border }]}>
      <Text allowFontScaling numberOfLines={2} style={{ flex: 1, color: t.text, fontSize: type.body }}>{selected || 'Chọn'}</Text><Ionicons name="chevron-down" size={18} color={t.muted} />
    </Pressable></View>
    <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
      <View style={[s.overlay, { justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.35)' }]}>
        <View style={{ maxHeight: '85%', padding: space.x4, borderTopLeftRadius: radius.panel, borderTopRightRadius: radius.panel, backgroundColor: t.bg, gap: space.x3 }}>
          <SectionHeader title={label} action={<IconButton label="Đóng danh sách" icon="close" onPress={() => setOpen(false)} />} />
          <Field label={`Tìm ${label}`} value={search} onChangeText={setSearch} autoCapitalize="none" />
          <FlatList keyboardShouldPersistTaps="handled" data={shown} keyExtractor={item => item.value} renderItem={({ item }) =>
            <ListItem title={item.label || '(Trống)'} icon={item.value === value ? 'checkmark-circle' : 'ellipse-outline'} onPress={() => { onChange(item.value); setOpen(false); }} />}
            ListEmptyComponent={<EmptyState title="Không có lựa chọn phù hợp" description="Thử từ khóa ngắn hơn hoặc xóa nội dung tìm." />} />
        </View>
      </View>
    </Modal>
  </>;
}

export function DateTimeInput({ label, value, onChange, mode = 'date', disabled = false, minimumDate, maximumDate }: {
  label: string; value: string; onChange: (value: string) => void; mode?: 'date' | 'time' | 'datetime'; disabled?: boolean; minimumDate?: Date; maximumDate?: Date;
}) {
  const t = useTheme(); const [open, setOpen] = useState(false); const [selected, setSelected] = useState<Date | null>(null);
  const initial = new Date(value || '2000-01-01T12:00:00'); const valid = Number.isFinite(initial.getTime()) ? initial : new Date('2000-01-01T12:00:00');
  const pad = (n: number) => String(n).padStart(2, '0');
  const encode = (date: Date) => mode === 'time' ? `${pad(date.getHours())}:${pad(date.getMinutes())}` : mode === 'datetime'
    ? `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
    : `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}`;
  const shown = mode === 'time' ? value : value ? new Date(value.length === 10 ? `${value}T12:00:00` : value).toLocaleString('vi-VN', mode === 'date' ? { dateStyle: 'medium' } : { dateStyle: 'medium', timeStyle: 'short' }) : 'Chọn ngày';
  const pick = () => {
    if (disabled) return;
    const start = value ? valid : new Date(); setSelected(start);
    if (Platform.OS === 'android') DateTimePickerAndroid.open({ value: start, mode: mode === 'datetime' ? 'date' : mode, minimumDate, maximumDate,
      onChange: (event, date) => { if (event.type !== 'set' || !date) return;
        if (mode === 'datetime') DateTimePickerAndroid.open({ value: date, mode: 'time', onChange: (next, time) => { if (next.type === 'set' && time) { date.setHours(time.getHours(), time.getMinutes()); onChange(encode(date)); } } });
        else onChange(encode(date));
      } });
    else setOpen(true);
  };
  return <>
    <View style={s.stack}><Copy>{label}</Copy><Pressable accessibilityRole="button" accessibilityLabel={`Chọn ${label}`} accessibilityState={{ disabled }} disabled={disabled} onPress={pick}
      style={({ pressed }) => [s.button, { flexDirection: 'row', justifyContent: 'flex-start', gap: space.x2, backgroundColor: t.surface, borderColor: t.border, opacity: pressed ? 0.75 : 1 }]}>
      <Ionicons name={mode === 'time' ? 'time-outline' : 'calendar-outline'} size={18} color={t.brand} /><Text allowFontScaling style={{ color: t.text, fontSize: type.body }}>{shown}</Text>
    </Pressable></View>
    {Platform.OS !== 'android' ? <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
      <View style={[s.overlay, { justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.35)' }]}><View style={{ padding: space.x4, borderTopLeftRadius: radius.panel, borderTopRightRadius: radius.panel, backgroundColor: t.bg }}>
        {Platform.OS === 'web' ? <Field label={label} value={value} onChangeText={onChange} /> : <DateTimePicker value={selected || valid} mode={mode === 'datetime' ? 'datetime' : mode} display="spinner" minimumDate={minimumDate} maximumDate={maximumDate} onChange={(_, date) => { if (date) onChange(encode(date)); }} />}
        <Button label="Xong" onPress={() => setOpen(false)} />
      </View></View>
    </Modal> : null}
  </>;
}

export function ErrorNote({ message }: { message: string }) {
  const t = useTheme();
  return message ? <View accessibilityRole="alert" style={[s.card, { borderColor: t.danger, backgroundColor: t.dangerBg }]}>
    <View style={[s.row, { gap: space.x2, flexWrap: 'nowrap' }]}><Ionicons name="alert-circle-outline" size={20} color={t.danger} /><Text allowFontScaling style={[s.body, { flex: 1, color: t.danger }]}>{message}</Text></View></View> : null;
}

export function Loading() { const t = useTheme(); return <ActivityIndicator color={t.brand} accessibilityLabel="Đang tải" />; }

export function Confirm({ title, detail, onConfirm, onCancel, busy, children }: PropsWithChildren<{
  title: string; detail: string; onConfirm: () => void; onCancel: () => void; busy: boolean;
}>) {
  const t = useTheme();
  return <Modal transparent animationType="slide" onRequestClose={() => { if (!busy) onCancel(); }}>
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={[s.overlay, { justifyContent: 'flex-end', padding: 0, backgroundColor: 'rgba(0,0,0,0.35)' }]}>
      <ScrollView keyboardShouldPersistTaps="handled" style={{ flexGrow: 0, width: '100%', maxHeight: '90%', maxWidth: 512, alignSelf: 'center', borderTopLeftRadius: radius.panel, borderTopRightRadius: radius.panel, backgroundColor: t.bg }} contentContainerStyle={{ padding: space.x4 }}>
        <Card><SectionHeader title={title} /><Copy>{detail}</Copy>{children}
          <Button label="Xác nhận" onPress={onConfirm} busy={busy} /><Button label="Quay lại" onPress={onCancel} variant="text" disabled={busy} />
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  </Modal>;
}

export function dateLabel(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : value;
}

export function moneyLabel(value: string) {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value);
  if (!match) return value;
  const fraction = (match[3] || '').replace(/0+$/, '');
  return match[1] + match[2].replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (fraction ? ',' + fraction : '');
}

export function useRows<T>(path: string) {
  const { request } = useSession();
  const sequence = useRef(0);
  type State = { path: string; data: Page<T> | null; loading: boolean; loadingMore: boolean; error: string };
  const initial: State = { path, data: null, loading: true, loadingMore: false, error: '' };
  const [state, setState] = useState<State>(initial);
  // Derive the new path's initial state immediately; never paint the old list
  // or an empty state while waiting for the focus effect to start its request.
  const { data, loading, loadingMore, error } = state.path === path ? state : initial;
  const load = useCallback(async (page = 1, append = false) => {
    const current = ++sequence.current;
    setState(previous => ({ ...(previous.path === path ? previous : { path, data: null }), loading: !append, loadingMore: append, error: '' }));
    try {
      const value = await request<Page<T>>(`${path}${path.includes('?') ? '&' : '?'}page=${page}`);
      if (current === sequence.current) setState(previous => ({ path, data: append && previous.path === path && previous.data
        ? { ...value, items: [...previous.data.items, ...value.items] } : value, loading: false, loadingMore: false, error: '' }));
    }
    catch (err) { if (current === sequence.current) setState(previous => ({ ...(previous.path === path ? previous : { path, data: null }),
      loading: false, loadingMore: false, error: err instanceof Error ? err.message : 'Không thể tải dữ liệu.' })); }
  }, [path, request]);
  useFocusEffect(useCallback(() => { void load(); return () => { sequence.current += 1; }; }, [load]));
  const loadMore = useCallback(() => { if (!loading && !loadingMore && !error && data?.has_next) void load(data.page+1, true); }, [data, error, load, loading, loadingMore]);
  return { data, loading, loadingMore, error, reload: () => load(), loadMore,
    controls: <View style={s.stack}><ErrorNote message={error} />{loading ? <Loading /> :
      <View style={s.row}><Button label="Tải lại" variant="secondary" onPress={() => void load(data?.page || 1)} />
        {data && data.page > 1 ? <Button label="Trang trước" variant="secondary" onPress={() => void load(data.page-1)} /> : null}
        {data?.has_next ? <Button label="Trang sau" variant="secondary" onPress={() => void load(data.page+1)} /> : null}</View>}
      {data ? <Copy muted>Trang {data.page} · {data.count} bản ghi</Copy> : null}</View> };
}
