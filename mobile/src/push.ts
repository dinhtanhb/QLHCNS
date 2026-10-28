import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';

export const pushConfigured = Platform.OS !== 'web' && Boolean(Constants.expoConfig?.extra?.eas?.projectId);

export async function enablePush() {
  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId || Platform.OS === 'web') throw new Error('Thông báo điện thoại chưa được cấu hình.');
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('ihrms-updates', {
      name: 'Cập nhật IHRMS', importance: AndroidImportance.DEFAULT,
    });
  }
  let permission = await Notifications.getPermissionsAsync();
  if (permission.status !== 'granted') permission = await Notifications.requestPermissionsAsync();
  if (permission.status !== 'granted') throw new Error('Chưa được cấp quyền thông báo. Bạn vẫn có thể xem thông báo trong ứng dụng.');
  return (await Notifications.getExpoPushTokenAsync({ projectId })).data;
}
