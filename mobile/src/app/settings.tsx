import { useCallback, useState } from 'react';
import { AppState, Linking, Platform, Pressable, Text, View } from 'react-native';
import { Redirect, router, useFocusEffect } from 'expo-router';
import * as Notifications from 'expo-notifications';
import { AppearanceMode, useAppearance } from '../appearance';
import { useSession } from '../session';
import { useTheme } from '../theme';
import { Button, Card, Copy, ErrorNote, Screen, s } from '../ui';
import { pushConfigured } from '../push';

export default function Settings() {
  const { me } = useSession();
  const { mode, ready, select } = useAppearance();
  const t = useTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [permission, setPermission] = useState('Đang kiểm tra quyền…');
  useFocusEffect(useCallback(() => {
    let active = true;
    const refresh = async () => {
      if (!pushConfigured) return;
      try {
        const value = await Notifications.getPermissionsAsync();
        if (active) setPermission(value.granted ? 'Đã cho phép thông báo' : 'Chưa cho phép thông báo');
      } catch { if (active) setPermission('Chưa kiểm tra được quyền thông báo'); }
    };
    void refresh();
    const listener = AppState.addEventListener('change', state => { if (state === 'active') void refresh(); });
    return () => { active = false; listener.remove(); };
  }, []));
  if (!me) return <Redirect href="/login" />;
  const change = (next: AppearanceMode) => {
    setBusy(true); setError('');
    void select(next).catch(() => setError('Chưa lưu được giao diện. Vui lòng thử lại.')).finally(() => setBusy(false));
  };
  return <Screen title="Cài đặt" description="Tài khoản và tùy chọn trên thiết bị này">
    <Button label="Quay lại hồ sơ" secondary onPress={() => router.replace('/(tabs)')} />
    <ErrorNote message={error} />
    <Card><Copy title>Tài khoản</Copy><Copy>{me.username}</Copy>
      {me.profile ? <Copy muted>{me.profile.full_name}</Copy> : null}
      <Button label="Đổi mật khẩu" secondary onPress={() => router.push('/password-change')} />
      {me.can_request_profile_change ? <Button label="Cập nhật thông tin cá nhân" secondary onPress={() => router.push('/profile-change')} /> : null}
      <Copy muted>Thông tin cá nhân được cập nhật sau khi Nhân sự duyệt yêu cầu.</Copy></Card>
    <Card><Copy title>Giao diện</Copy><Copy muted>Lựa chọn được lưu trên thiết bị và áp dụng cho mọi màn hình.</Copy>
      <View accessibilityRole="radiogroup" style={s.stack}>
        {([{ value: 'system', label: 'Theo điện thoại' }, { value: 'light', label: 'Sáng' }, { value: 'dark', label: 'Tối' }] as const).map(item =>
          <Pressable key={item.value} accessibilityRole="radio" accessibilityLabel={item.label}
            aria-checked={mode === item.value}
            {...(Platform.OS === 'web' ? { onKeyDown: (event: unknown) => {
              if (!busy && ready && event && typeof event === 'object' && 'key' in event &&
                  (event.key === ' ' || event.key === 'Enter') && 'preventDefault' in event && typeof event.preventDefault === 'function') {
                event.preventDefault(); change(item.value);
              }
            } } : {})}
            accessibilityState={{ checked: mode === item.value, disabled: busy || !ready }} disabled={busy || !ready}
            onPress={() => change(item.value)} style={[s.button, { borderColor: mode === item.value ? t.brand : t.border, backgroundColor: t.surface }]}>
            <Text style={[s.buttonText, { color: t.text }]}>{mode === item.value ? '✓ ' : ''}{item.label}</Text>
          </Pressable>)}
      </View><Copy muted>“Theo điện thoại” tự thay đổi theo cài đặt sáng/tối của hệ thống.</Copy></Card>
    {pushConfigured ? <Card><Copy title>Quyền thông báo</Copy><Copy>{permission}</Copy>
      <Copy muted>Quyền trên điện thoại cho phép hiển thị lời nhắc. Thiết bị cần có Internet và tài khoản còn đăng nhập để nhận thông báo.</Copy>
      {Platform.OS !== 'web' ? <Button label="Mở cài đặt điện thoại" secondary onPress={() => {
        void Linking.openSettings().catch(() => setError('Không mở được cài đặt. Hãy mở Cài đặt điện thoại → Ứng dụng → IHRMS QA.'));
      }} /> : null}</Card> : null}
  </Screen>;
}
