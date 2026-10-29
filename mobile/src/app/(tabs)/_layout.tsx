import { Redirect, Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Loading, Screen } from '../../ui';
import { ConfiguredPushNavigation } from '../../PushNavigation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function TabsLayout() {
  const { me, ready } = useSession(); const t = useTheme();
  const insets = useSafeAreaInsets();
  if (!ready) return <Screen title="IHRMS"><Loading /></Screen>;
  if (!me) return <Redirect href="/login" />;
  const icons = { index: 'home-outline', profile: 'person-outline', attendance: 'calendar-outline', leaves: 'document-text-outline', approvals: 'checkmark-circle-outline', notifications: 'notifications-outline' } as const;
  return <><ConfiguredPushNavigation /><Tabs screenOptions={({ route }) => ({ headerShown: false, tabBarActiveTintColor: t.brand,
    tabBarInactiveTintColor: t.muted, tabBarStyle: { backgroundColor: t.surface, borderTopColor: t.cardBorder,
      height: 72 + insets.bottom, paddingBottom: insets.bottom, paddingTop: 8 },
    tabBarLabelStyle: { fontSize: 12, fontWeight: '600' },
    tabBarIcon: ({ color, size }) => <Ionicons name={icons[route.name as keyof typeof icons]} size={size} color={typeof color === 'string' ? color : t.text} />,
  })}>
    <Tabs.Screen name="index" options={{ title: 'Trang chủ', tabBarAccessibilityLabel: 'Trang chủ' }} />
    <Tabs.Screen name="profile" options={{ title: 'Tôi', tabBarAccessibilityLabel: 'Tôi' }} />
    <Tabs.Screen name="attendance" options={{ title: 'Chấm công', tabBarAccessibilityLabel: 'Chấm công' }} />
    <Tabs.Screen name="leaves" options={{ title: 'Nghỉ phép', tabBarAccessibilityLabel: 'Nghỉ phép' }} />
    <Tabs.Screen name="approvals" options={{ title: 'Duyệt đơn', tabBarAccessibilityLabel: 'Duyệt đơn', tabBarButton: () => null }} />
    <Tabs.Screen name="notifications" options={{ title: 'Thông báo', tabBarAccessibilityLabel: 'Thông báo' }} />
  </Tabs></>;
}
