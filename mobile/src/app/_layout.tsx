import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SessionProvider } from '../session';
import { useNetworkState } from 'expo-network';
import { Copy, Screen } from '../ui';

function Routes() {
  const network = useNetworkState();
  if (network.isConnected === false) return <Screen title="Không có kết nối"><Copy>Kết nối lại mạng để sử dụng IHRMS. Các thao tác chưa gửi sẽ không tự động gửi lại.</Copy></Screen>;
  return <Stack screenOptions={{ headerShown: false }} />;
}

export default function RootLayout() {
  return <SafeAreaProvider><SessionProvider><StatusBar style="auto" />
    <Routes />
  </SessionProvider></SafeAreaProvider>;
}
