import { useColorScheme } from 'react-native';
import { useSession } from './session';
import palettes from './palettes.json';

export function useTheme() {
  const { me } = useSession();
  const mode = useColorScheme() === 'dark' ? 'dark' : 'light';
  return palettes[me?.palette || 'viethealth'][mode];
}
