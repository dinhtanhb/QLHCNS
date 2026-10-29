import { useState } from 'react';
import { Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Field, Screen } from '../ui';

export default function PasswordChange() {
  const { me, changePassword } = useSession();
  const [old, setOld] = useState(''); const [next, setNext] = useState(''); const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Đổi mật khẩu" description="Bạn sẽ đăng nhập lại sau khi đổi mật khẩu thành công.">
    <Button label="Quay lại cài đặt" secondary disabled={busy} onPress={() => router.replace('/settings')} />
    <Card><Copy muted>Dùng mật khẩu đủ mạnh, tránh tên tài khoản và thông tin cá nhân.</Copy>
      <Field label="Mật khẩu hiện tại" value={old} onChangeText={setOld} secureTextEntry autoCapitalize="none" autoCorrect={false} autoComplete="current-password" maxLength={1024} editable={!busy} />
      <Field label="Mật khẩu mới" value={next} onChangeText={setNext} secureTextEntry autoCapitalize="none" autoCorrect={false} autoComplete="new-password" maxLength={1024} editable={!busy} />
      <Field label="Nhập lại mật khẩu mới" value={confirm} onChangeText={setConfirm} secureTextEntry autoCapitalize="none" autoCorrect={false} autoComplete="new-password" maxLength={1024} editable={!busy} />
      <ErrorNote message={error} /><Button label="Lưu mật khẩu mới" busy={busy} disabled={!old || !next || !confirm} onPress={() => {
        if (next !== confirm) { setError('Hai mật khẩu mới chưa khớp.'); return; }
        setBusy(true); setError('');
        void changePassword(old, next, confirm).then(() => { setOld(''); setNext(''); setConfirm(''); router.replace('/login'); })
          .catch(e => { setOld(''); setNext(''); setConfirm(''); setError(e.message); }).finally(() => setBusy(false));
      }} /></Card>
  </Screen>;
}
