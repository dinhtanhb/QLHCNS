import { useState } from 'react';
import { View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Field, Screen, s, useRows } from '../ui';

type Change = { id: number; field_label: string; new_value: string; status_label: string; decision_note: string };
const fields = [{ key: 'personal_email', label: 'Email cá nhân' }, { key: 'mobile_phone', label: 'Số điện thoại' }, { key: 'address', label: 'Địa chỉ' }] as const;
export default function ProfileChange() {
  const { me, request } = useSession();
  const [field, setField] = useState<typeof fields[number]['key']>('personal_email');
  const [value, setValue] = useState(''); const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  const rows = useRows<Change>('profile-requests/');
  if (!me) return <Redirect href="/login" />;
  if (!me.can_request_profile_change) return <Screen title="Cập nhật thông tin cá nhân"><Copy>Tài khoản chưa có quyền gửi yêu cầu cập nhật.</Copy></Screen>;
  return <Screen title="Cập nhật thông tin cá nhân" description="Gửi yêu cầu cho Nhân sự duyệt. Hồ sơ hiện tại chưa thay đổi khi gửi.">
    <Button label="Quay lại cài đặt" secondary disabled={busy} onPress={() => router.replace('/settings')} />
    <Card><Copy title>Thông tin hiện tại</Copy>{fields.map(item => <Copy key={item.key}>{item.label}: {me.profile?.[item.key] || 'Chưa có'}</Copy>)}</Card>
    <Card><Copy title>Gửi yêu cầu cập nhật</Copy><View style={s.stack}>{fields.map(item =>
      <Button key={item.key} label={`${field === item.key ? '✓ ' : ''}${item.label}`} secondary disabled={busy} onPress={() => { setField(item.key); setValue(''); setMessage(''); }} />)}</View>
      <Field label="Thông tin mới" value={value} onChangeText={setValue} maxLength={field === 'address' ? 500 : 150} autoCapitalize="none" autoCorrect={false} editable={!busy} />
      <Field label="Lý do cập nhật" value={reason} onChangeText={setReason} maxLength={500} multiline editable={!busy} />
      <ErrorNote message={error} />{message ? <Copy>{message}</Copy> : null}
      <Button label="Gửi yêu cầu cập nhật" busy={busy} disabled={!value.trim()} onPress={() => {
        setBusy(true); setError(''); setMessage('');
        void request('profile-requests/', { field_name: field, new_value: value, reason }).then(() => {
          setValue(''); setReason(''); setMessage('Đã gửi yêu cầu đến Nhân sự.'); void rows.reload();
        }).catch(e => setError(e.message)).finally(() => setBusy(false));
      }} /></Card>
    <Copy title>Yêu cầu của tôi</Copy>{rows.controls}{rows.data?.items.map(item =>
      <Card key={item.id}><Copy title>{item.field_label} · {item.status_label}</Copy><Copy>{item.new_value}</Copy>{item.decision_note ? <Copy muted>{item.decision_note}</Copy> : null}</Card>)}
  </Screen>;
}
