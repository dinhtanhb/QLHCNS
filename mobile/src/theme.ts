import { useAppearance } from './appearance';
import { useSession } from './session';
import palettes from './palettes.json';

export function useTheme() {
  const { me } = useSession();
  const mode = useAppearance().dark ? 'dark' : 'light';
  return palettes[me?.palette || 'viethealth'][mode];
}
