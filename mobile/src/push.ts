import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';

export const pushConfigured = Platform.OS !== 'web' && Boolean(Constants.expoConfig?.extra?.eas?.projectId);

// Keep foreground presentation explicit instead of relying on SDK defaults.
if (pushConfigured) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true, shouldShowList: true,
      shouldPlaySound: true, shouldSetBadge: false,
    }),
  });
}

async function getExpoToken(requestPermission: boolean): Promise<string | null> {
  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId || Platform.OS === 'web') return null;
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('ihrms-updates', {
      name: 'Cập nhật IHRMS', importance: AndroidImportance.HIGH, sound: 'default',
    });
  }
  let permission = await Notifications.getPermissionsAsync();
  if (permission.status !== 'granted' && requestPermission) {
    permission = await Notifications.requestPermissionsAsync();
  }
  if (permission.status !== 'granted') return null;
  return (await Notifications.getExpoPushTokenAsync({ projectId })).data;
}

// Check silently on app launch/resume. Asking Android to show its permission
// dialog remains an explicit action initiated by the user in their profile.
export const getGrantedPushToken = () => getExpoToken(false);

export async function enablePush() {
  const token = await getExpoToken(true);
  if (!token) throw new Error('Chưa được cấp quyền thông báo. Bạn vẫn có thể xem thông báo trong ứng dụng.');
  return token;
}
