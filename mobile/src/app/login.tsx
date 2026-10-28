import { useState } from 'react';
import { Image, KeyboardAvoidingView, Platform, Text } from 'react-native';
import { Redirect } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Field, Loading, Screen, s } from '../ui';
import { useTheme } from '../theme';

export default function LoginScreen() {
  const session = useSession(); const t = useTheme();
  const [server, setServer] = useState(process.env.EXPO_PUBLIC_API_URL || (Platform.OS === 'web' ? window.location.origin : ''));
  const [username, setUsername] = useState(''); const [password, setPassword] = useState('');
  if (!session.ready) return <Screen title="IHRMS"><Loading /></Screen>;
  if (session.me) return <Redirect href="/(tabs)" />;
  const submit = () => {
    void session.login(server, username, password).then(() => setPassword('')).catch(() => setPassword(''));
  };
  return <KeyboardAvoidingView style={s.page} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
    <Screen title="IHRMS" description="Cổng nhân sự nội bộ VietHealth">
      <Image source={require('../../assets/logo.png')} style={{ width: 192, height: 96, alignSelf: 'center' }} resizeMode="contain" accessibilityLabel="VietHealth" />
      <Card><Text style={[s.title, { color: t.text }]}>Chào mừng trở lại</Text><Copy muted>Đăng nhập bằng tài khoản IHRMS của bạn.</Copy>
        {!process.env.EXPO_PUBLIC_API_URL ? <Field label="Địa chỉ IHRMS" value={server} onChangeText={setServer}
          autoCapitalize="none" autoCorrect={false} keyboardType="url" placeholder="https://nhansu.congty.vn" editable={!session.busy} /> : null}
        <Field label="Tên đăng nhập" value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false}
          autoComplete="username" textContentType="username" editable={!session.busy} maxLength={150} />
        <Field label="Mật khẩu" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password"
          textContentType="password" editable={!session.busy} maxLength={1024} onSubmitEditing={submit} returnKeyType="go" />
        <ErrorNote message={session.error} />
        <Button label="Đăng nhập" onPress={submit} busy={session.busy} disabled={!server || !username.trim() || !password} />
      </Card><Copy muted>Ứng dụng dành cho nhân viên được cấp quyền. Liên hệ bộ phận Nhân sự nếu bạn cần hỗ trợ tài khoản.</Copy>
    </Screen>
  </KeyboardAvoidingView>;
}
