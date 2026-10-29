import { useCallback, useState } from 'react';
import { KeyboardAvoidingView, Platform, View } from 'react-native';
import { Redirect, router, useFocusEffect } from 'expo-router';
import { Button, Card, Copy, ErrorNote, Field, Loading, Screen, s } from '../ui';
import type { LeaveOptions } from '../types';
import { useSession } from '../session';

function isoDate(raw: string) {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(raw.trim());
  if (!match) throw new Error('Ngày cần có dạng DD/MM/YYYY.');
  const iso = `${match[3]}-${match[2]}-${match[1]}`;
  const value = new Date(iso+'T12:00:00Z');
  if (!Number.isFinite(value.getTime()) || value.toISOString().slice(0, 10) !== iso) throw new Error('Ngày không hợp lệ.');
  return iso;
}

export default function NewLeave() {
  const { me, request } = useSession();
  const [options, setOptions] = useState<LeaveOptions | null>(null);
  const [kind, setKind] = useState<number | null>(null); const [from, setFrom] = useState(''); const [to, setTo] = useState('');
  const [reason, setReason] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const load = useCallback(() => { setError(''); void request<LeaveOptions>('leave-options/').then(setOptions).catch(e => setError(e.message)); }, [request]);
  useFocusEffect(load);
  if (!me) return <Redirect href="/login" />;
  const submit = async () => {
    if (busy) return;
    setError('');
    try {
      if (!kind) throw new Error('Vui lòng chọn loại nghỉ.');
      const fromDate = isoDate(from), toDate = isoDate(to);
      if (toDate < fromDate) throw new Error('Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.');
      setBusy(true);
      await request('leaves/', { leave_type: kind, from_date: fromDate, to_date: toDate, reason: reason.trim() });
      router.replace({ pathname: '/(tabs)/my-work', params: { section: 'leave', submitted: String(Date.now()) } });
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể gửi đơn.'); }
    finally { setBusy(false); }
  };
  return <KeyboardAvoidingView style={s.page} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
    <Screen title="Tạo đơn nghỉ phép" description="Ngày nghỉ và hạn mức được kiểm tra khi gửi">
      <ErrorNote message={error} />
      {!options ? <View style={s.stack}>{error ? <Button label="Thử tải lại" secondary onPress={load} /> : <Loading />}</View> :
        !options.can_submit ? <Card><Copy>Tài khoản chưa gắn hồ sơ nhân viên. Vui lòng liên hệ Nhân sự.</Copy></Card> :
          <Card><Copy title>Loại nghỉ</Copy><View style={s.stack}>{options.types.map(item => <Button key={item.id}
            label={`${kind === item.id ? 'Đã chọn: ' : ''}${item.leave_type_name}`} secondary={kind !== item.id}
            disabled={busy} onPress={() => setKind(item.id)} />)}</View>
            <Field label="Từ ngày (DD/MM/YYYY)" value={from} onChangeText={setFrom} placeholder="02/11/2026" maxLength={10} editable={!busy} keyboardType="numbers-and-punctuation" />
            <Field label="Đến ngày (DD/MM/YYYY)" value={to} onChangeText={setTo} placeholder="02/11/2026" maxLength={10} editable={!busy} keyboardType="numbers-and-punctuation" />
            <Field label="Lý do nghỉ" value={reason} onChangeText={setReason} multiline maxLength={500} editable={!busy} style={{ minHeight: 96, textAlignVertical: 'top' }} />
            <Copy muted>{reason.length}/500 ký tự</Copy><Button label="Gửi đơn nghỉ phép" busy={busy} onPress={() => void submit()} disabled={!kind || !from || !to} />
          </Card>}
    <Button label="Quay lại danh sách" secondary disabled={busy} onPress={() => router.replace('/(tabs)/my-work?section=leave')} />
    </Screen>
  </KeyboardAvoidingView>;
}
