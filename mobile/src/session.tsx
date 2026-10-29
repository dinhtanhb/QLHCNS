import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AppState, Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { ApiError, call, serverURL } from './api';
import type { Me } from './types';

type Credentials = { server: string; token: string; expires_at: string };
type Session = {
  me: Me | null; ready: boolean; busy: boolean; error: string;
  login: (server: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (old_password: string, new_password: string, confirm_password: string) => Promise<void>;
  request: <T>(path: string, data?: unknown) => Promise<T>;
  refreshMe: () => Promise<void>;
};
const Context = createContext<Session | null>(null);
const KEY = 'ihrms.mobile.session';
const persist = async (value: Credentials | null) => {
  if (Platform.OS === 'web') return; // Browser QA keeps bearer only in memory.
  if (value) await SecureStore.setItemAsync(KEY, JSON.stringify(value), { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY });
  else await SecureStore.deleteItemAsync(KEY);
};

export function SessionProvider({ children }: PropsWithChildren) {
  const credentials = useRef<Credentials | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const forget = useCallback(async () => {
    credentials.current = null; setMe(null);
    await persist(null);
  }, []);
  const request = useCallback(async <T,>(path: string, data?: unknown): Promise<T> => {
    const current = credentials.current;
    if (!current) throw new ApiError('Vui lòng đăng nhập lại.', 401);
    try { return await call<T>(current.server, current.token, path, data); }
    catch (err) {
      if (err instanceof ApiError && err.status === 401 && credentials.current === current) {
        await forget(); setError('Phiên đã hết hạn. Vui lòng đăng nhập lại.');
      }
      throw err;
    }
  }, [forget]);
  const refreshMe = useCallback(async () => {
    const current = credentials.current;
    const value = await request<Me>('me/');
    if (credentials.current === current) { setMe(value); setError(''); }
  }, [request]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const raw = Platform.OS === 'web' ? null : await SecureStore.getItemAsync(KEY);
        if (raw) {
          const saved = JSON.parse(raw) as Credentials;
          const fixed = process.env.EXPO_PUBLIC_API_URL;
          if (!saved.token || !Number.isFinite(Date.parse(saved.expires_at)) || Date.parse(saved.expires_at) <= Date.now()
              || (fixed && serverURL(fixed) !== saved.server)) { await persist(null); return; }
          saved.server = serverURL(saved.server);
          // Retain the saved session while the server is temporarily unreachable.
          // Foreground revalidation can then recover without another login.
          if (alive) credentials.current = saved;
          const value = await call<Me>(saved.server, saved.token, 'me/');
          if (alive) { credentials.current = saved; setMe(value); }
        }
      } catch (err) {
        if (err instanceof SyntaxError || (err instanceof ApiError && err.status === 401)) {
          if (alive) credentials.current = null;
          await persist(null).catch(() => undefined);
        }
        if (alive) setError(err instanceof Error ? err.message : 'Không thể mở phiên đăng nhập.');
      } finally { if (alive) setReady(true); }
    })();
    return () => { alive = false; };
  }, []);

  // Revalidate whenever returning to the foreground, before showing old records.
  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      if (state === 'active' && credentials.current) void refreshMe().catch(err => setError(err.message));
    });
    return () => subscription.remove();
  }, [refreshMe]);

  // Recover a saved session after startup network failures, without requiring
  // the user to close the app or enter their password again.
  useEffect(() => {
    if (!ready || me || !credentials.current) return;
    const retry = setInterval(() => {
      void refreshMe().catch(err => setError(err.message));
    }, 15000);
    return () => clearInterval(retry);
  }, [ready, me, refreshMe]);

  const login = async (raw: string, username: string, password: string) => {
    setBusy(true); setError('');
    let issued: Credentials | null = null;
    try {
      const server = serverURL(process.env.EXPO_PUBLIC_API_URL || raw);
      const result = await call<{ token: string; expires_at: string }>(server, null, 'login/', { username: username.trim(), password });
      issued = { server, ...result };
      const value = await call<Me>(server, issued.token, 'me/');
      await persist(issued); credentials.current = issued; setMe(value);
    } catch (err) {
      if (issued) await call(issued.server, issued.token, 'logout/', {}).catch(() => undefined);
      setError(err instanceof Error ? err.message : 'Không thể đăng nhập.');
      throw err;
    } finally { setBusy(false); }
  };
  const logout = async () => {
    setBusy(true); setError('');
    try {
      // Keep session on a network failure so the user can retry server revocation.
      await request('logout/', {}); await forget();
    } catch (err) { setError(err instanceof Error ? err.message : 'Chưa thể đăng xuất.'); throw err; }
    finally { setBusy(false); }
  };
  const changePassword = async (old_password: string, new_password: string, confirm_password: string) => {
    await request('change-password/', { old_password, new_password, confirm_password });
    await forget();
  };
  return <Context.Provider value={{ me, ready, busy, error, login, logout, changePassword, request, refreshMe }}>{children}</Context.Provider>;
}

export function useSession() {
  const value = useContext(Context);
  if (!value) throw new Error('SessionProvider is required');
  return value;
}
