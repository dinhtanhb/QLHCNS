import type { ExpoConfig } from 'expo/config';

const qa = process.env.MOBILE_VARIANT !== 'production';
const api = process.env.EXPO_PUBLIC_API_URL;
const projectId = process.env.EXPO_PUBLIC_EAS_PROJECT_ID || (qa ? '53634c3e-75ad-4a4c-895c-28e298b63256' : undefined);
if (!qa) {
  if (!api || !/^https:\/\/[^/@?#]+\/?$/.test(api) || process.env.EXPO_PUBLIC_ALLOW_HTTP === 'true') {
    throw new Error('Production requires a fixed HTTPS EXPO_PUBLIC_API_URL and HTTP disabled.');
  }
}
const config: ExpoConfig = {
  name: qa ? 'IHRMS QA' : 'IHRMS', slug: qa ? 'ihrms' : 'ihrms-internal', version: '1.0.0',
  ...(qa ? { owner: 'viethealth.org.vn' } : {}),
  scheme: qa ? 'ihrms-qa' : 'ihrms', userInterfaceStyle: 'automatic', orientation: 'default',
  icon: './assets/app-icon.png',
  ios: { supportsTablet: true, bundleIdentifier: qa ? 'vn.ihrms.internal.qa' : 'vn.ihrms.internal',
    infoPlist: { ITSAppUsesNonExemptEncryption: false } },
  android: { package: qa ? 'vn.ihrms.internal.qa' : 'vn.ihrms.internal',
    ...(process.env.MOBILE_GOOGLE_SERVICES_FILE ? { googleServicesFile: process.env.MOBILE_GOOGLE_SERVICES_FILE } : {}),
    permissions: ['POST_NOTIFICATIONS'],
    blockedPermissions: ['android.permission.RECORD_AUDIO', 'android.permission.CAMERA',
      'android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE'],
    adaptiveIcon: { foregroundImage: './assets/app-icon.png', backgroundColor: '#ffffff' } },
  web: { bundler: 'metro', output: 'single', favicon: './assets/app-icon.png' },
  plugins: ['expo-router', 'expo-secure-store', 'expo-notifications', './plugins/with-short-cmake-paths',
    ['expo-build-properties', { android: { usesCleartextTraffic: qa && process.env.EXPO_PUBLIC_ALLOW_HTTP === 'true' } }]],
  extra: { qa, ...(projectId ? { eas: { projectId } } : {}) },
};
export default config;
