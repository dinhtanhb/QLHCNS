import { Redirect, Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Loading, Screen } from '../../ui';
import { ConfiguredPushNavigation } from '../../PushNavigation';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ApprovalInboxProvider, useApprovalInbox } from '../../approval-inbox';

export default function TabsLayout() {
  const { me, ready } = useSession();
  if (!ready) return <Screen title="IHRMS"><Loading /></Screen>;
  if (!me) return <Redirect href="/login" />;
  return <ApprovalInboxProvider><TabNavigator /></ApprovalInboxProvider>;
}

function TabNavigator() {
  const { me } = useSession(); const t = useTheme(); const insets = useSafeAreaInsets();
  const { count: pending, refreshCount } = useApprovalInbox();
  if (!me) return null;
  const icons: Record<string, React.ComponentProps<typeof Ionicons>['name']> = {
    index: 'home-outline', 'my-work': 'briefcase-outline', approvals: 'checkmark-circle-outline', notifications: 'notifications-outline', more: 'grid-outline',
  };
  const tabs = [
    ['index', 'Trang chủ'], ['my-work', 'Việc của tôi'], ...(me.can_approve ? [['approvals', 'Duyệt'] as string[]] : []),
    ['notifications', 'Thông báo'], ['more', 'Thêm'],
  ];
  return <><ConfiguredPushNavigation /><Tabs screenListeners={{ focus: () => { void refreshCount(); } }} screenOptions={({ route }) => ({ headerShown: false, tabBarActiveTintColor: t.brand,
    tabBarInactiveTintColor: t.muted, tabBarStyle: { backgroundColor: t.surface, borderTopColor: t.cardBorder,
      height: 68 + insets.bottom, paddingBottom: Math.max(insets.bottom, 6), paddingTop: 5 },
    tabBarLabelStyle: { fontSize: 11, fontWeight: '600' }, tabBarItemStyle: { minHeight: 58 },
    tabBarIcon: ({ color, size }) => <Ionicons name={icons[route.name] || 'ellipse-outline'} size={size} color={typeof color === 'string' ? color : t.text} />,
  })}>
    {tabs.map(([name, title]) => <Tabs.Screen key={name} name={name} options={{ title, tabBarAccessibilityLabel: title,
      ...(name === 'approvals' ? { tabBarBadge: pending !== null && pending > 0 ? (pending > 99 ? '99+' : pending) : undefined, tabBarBadgeStyle: { backgroundColor: t.danger, color: t.onBrand } } : {}),
    }} />)}
    {!me.can_approve ? <Tabs.Screen name="approvals" options={{ href: null }} /> : null}
    <Tabs.Screen name="attendance" options={{ href: null }} />
    <Tabs.Screen name="leaves" options={{ href: null }} />
    <Tabs.Screen name="profile" options={{ href: null }} />
  </Tabs></>;
}
