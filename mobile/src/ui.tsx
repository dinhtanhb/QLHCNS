import { PropsWithChildren, useCallback, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, TextInputProps, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from './theme';
import { useSession } from './session';
import type { Page } from './types';

export const s = StyleSheet.create({
  page: { flex: 1 }, content: { padding: 24, gap: 24, width: '100%', maxWidth: 768, alignSelf: 'center', paddingBottom: 48 },
  card: { borderWidth: 1, borderRadius: 8, padding: 16, gap: 12 },
  row: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12 },
  between: { justifyContent: 'space-between' }, stack: { gap: 8 }, grow: { flex: 1 },
  heading: { fontSize: 24, lineHeight: 32, fontWeight: '600' }, title: { fontSize: 18, lineHeight: 26, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24 }, small: { fontSize: 14, lineHeight: 20 },
  button: { minHeight: 48, paddingHorizontal: 16, paddingVertical: 12, borderRadius: 8, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  buttonText: { fontSize: 16, lineHeight: 24, fontWeight: '600', textAlign: 'center' },
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 12, fontSize: 16, minHeight: 48 },
  overlay: { flex: 1, justifyContent: 'center', padding: 24 },
});

export function Copy({ children, muted = false, title = false }: PropsWithChildren<{ muted?: boolean; title?: boolean }>) {
  const t = useTheme(); return <Text style={[title ? s.title : s.body, { color: muted ? t.muted : t.text }]}>{children}</Text>;
}
export function Screen({ title, description, children }: PropsWithChildren<{ title: string; description?: string }>) {
  const t = useTheme();
  return <SafeAreaView edges={['top', 'left', 'right']} style={[s.page, { backgroundColor: t.bg }]}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
      <View style={s.stack}><Text accessibilityRole="header" style={[s.heading, { color: t.text }]}>{title}</Text>
        {description ? <Copy muted>{description}</Copy> : null}</View>{children}
    </ScrollView>
  </SafeAreaView>;
}
export function Card({ children }: PropsWithChildren) {
  const t = useTheme(); return <View style={[s.card, { backgroundColor: t.surface, borderColor: t.cardBorder }]}>{children}</View>;
}
export function Button({ label, onPress, secondary = false, disabled = false, busy = false }: {
  label: string; onPress: () => void; secondary?: boolean; disabled?: boolean; busy?: boolean;
}) {
  const t = useTheme();
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled: disabled || busy, busy }}
    disabled={disabled || busy} onPress={onPress}
    style={({ pressed }) => [s.button, { backgroundColor: secondary ? t.surface : t.brand,
      borderColor: secondary ? t.border : t.brand, opacity: disabled || busy ? 0.6 : pressed ? 0.8 : 1 }]}>
    {busy ? <ActivityIndicator color={secondary ? t.text : t.onBrand} accessibilityLabel="Đang xử lý" />
      : <Text style={[s.buttonText, { color: secondary ? t.text : t.onBrand }]}>{label}</Text>}
  </Pressable>;
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  const t = useTheme();
  return <View style={s.stack}><Copy>{label}</Copy><TextInput accessibilityLabel={label} placeholderTextColor={t.muted}
    {...props} style={[s.input, { color: t.text, borderColor: t.border, backgroundColor: t.surface }, props.style]} /></View>;
}
export function ErrorNote({ message }: { message: string }) {
  const t = useTheme();
  return message ? <View accessibilityRole="alert" style={[s.card, { borderColor: t.danger, backgroundColor: t.dangerBg }]}>
    <Text style={[s.body, { color: t.danger }]}>{message}</Text></View> : null;
}
export function Loading() { const t = useTheme(); return <ActivityIndicator color={t.brand} accessibilityLabel="Đang tải" />; }
export function Confirm({ title, detail, onConfirm, onCancel, busy }: {
  title: string; detail: string; onConfirm: () => void; onCancel: () => void; busy: boolean;
}) {
  const t = useTheme();
  return <Modal transparent animationType="fade" onRequestClose={() => { if (!busy) onCancel(); }}>
    <View style={[s.overlay, { backgroundColor: t.bg }]}><View style={{ width: '100%', maxWidth: 512, alignSelf: 'center' }}>
      <Card><Text accessibilityRole="header" style={[s.title, { color: t.text }]}>{title}</Text><Copy>{detail}</Copy>
        <Button label="Xác nhận" onPress={onConfirm} busy={busy} /><Button label="Quay lại" onPress={onCancel} secondary disabled={busy} />
      </Card></View></View>
  </Modal>;
}
export function dateLabel(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : value;
}

export function useRows<T>(path: string) {
  const { request } = useSession();
  const [data, setData] = useState<Page<T> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async (page = 1) => {
    setLoading(true); setError(''); setData(null);
    try { setData(await request<Page<T>>(`${path}?page=${page}`)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Không thể tải dữ liệu.'); }
    finally { setLoading(false); }
  }, [path, request]);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  return { data, loading, error, reload: () => load(),
    controls: <View style={s.stack}><ErrorNote message={error} />{loading ? <Loading /> :
      <View style={s.row}><Button label="Tải lại" onPress={() => void load(data?.page || 1)} secondary />
        {data && data.page > 1 ? <Button label="Trang trước" secondary onPress={() => void load(data.page-1)} /> : null}
        {data?.has_next ? <Button label="Trang sau" secondary onPress={() => void load(data.page+1)} /> : null}</View>}
      {data ? <Copy muted>Trang {data.page} · {data.count} bản ghi</Copy> : null}</View> };
}
