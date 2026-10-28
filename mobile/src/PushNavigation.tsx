import { useEffect } from 'react';
import { router } from 'expo-router';
import * as Notifications from 'expo-notifications';
import { pushConfigured } from './push';

export default function PushNavigation() {
  const response = Notifications.useLastNotificationResponse();
  useEffect(() => {
    if (response?.notification.request.content.data?.screen === 'notifications') {
      router.push('/(tabs)/notifications');
      Notifications.clearLastNotificationResponse();
    }
  }, [response]);
  return null;
}

export function ConfiguredPushNavigation() {
  return pushConfigured ? <PushNavigation /> : null;
}
