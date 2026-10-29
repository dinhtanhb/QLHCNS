import { createContext, PropsWithChildren, useContext, useEffect, useRef, useState } from 'react';
import { Platform, useColorScheme } from 'react-native';
import * as SecureStore from 'expo-secure-store';

export type AppearanceMode = 'system' | 'light' | 'dark';
const KEY = 'ihrms.mobile.appearance';
const valid = (value: unknown): value is AppearanceMode => value === 'system' || value === 'light' || value === 'dark';
const Context = createContext<{
  mode: AppearanceMode; dark: boolean; ready: boolean;
  select: (mode: AppearanceMode) => Promise<void>;
} | null>(null);

export function AppearanceProvider({ children }: PropsWithChildren) {
  const system = useColorScheme();
  const [mode, setMode] = useState<AppearanceMode>('system');
  const [ready, setReady] = useState(false);
  const chosen = useRef(false);
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const saved = Platform.OS === 'web' ? window.localStorage.getItem(KEY) : await SecureStore.getItemAsync(KEY);
        if (alive && !chosen.current && valid(saved)) setMode(saved);
      } catch { /* Fall back to the phone preference if local storage is unavailable. */ }
      finally { if (alive) setReady(true); }
    })();
    return () => { alive = false; };
  }, []);
  const select = async (value: AppearanceMode) => {
    if (!valid(value)) return;
    chosen.current = true;
    // Commit the selection only after persistence succeeds so the UI never
    // reports a saved preference when the device rejected the write.
    if (Platform.OS === 'web') window.localStorage.setItem(KEY, value);
    else await SecureStore.setItemAsync(KEY, value);
    setMode(value);
  };
  return <Context.Provider value={{ mode, dark: mode === 'system' ? system === 'dark' : mode === 'dark', ready, select }}>
    {children}
  </Context.Provider>;
}

export function useAppearance() {
  const value = useContext(Context);
  if (!value) throw new Error('AppearanceProvider is required');
  return value;
}
