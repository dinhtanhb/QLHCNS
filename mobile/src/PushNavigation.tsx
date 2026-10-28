import { useEffect, useRef } from 'react';
import { AppState } from 'react-native';
import { router } from 'expo-router';
import * as Notifications from 'expo-notifications';
import { getGrantedPushToken, pushConfigured } from './push';
import { useSession } from './session';

export default function PushNavigation() {
  const response = Notifications.useLastNotificationResponse();
  const { request } = useSession();
  const registrationInFlight = useRef(false);

  useEffect(() => {
    let mounted = true;
    const registerIfAllowed = async () => {
      if (registrationInFlight.current) return;
      registrationInFlight.current = true;
      try {
        const token = await getGrantedPushToken();
        if (mounted && token) await request('push-token/', { token });
      } catch {
        // Retry on the next foreground; offline startup must not block the app.
      } finally {
        registrationInFlight.current = false;
      }
    };

    void registerIfAllowed();
    const subscription = AppState.addEventListener('change', state => {
      if (state === 'active') void registerIfAllowed();
    });
    return () => {
      mounted = false;
      subscription.remove();
    };
  }, [request]);

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
