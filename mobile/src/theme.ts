import { useAppearance } from './appearance';
import { useSession } from './session';
import { palettes } from './tokens';

export function useTheme() {
  const { me } = useSession();
  const mode = useAppearance().dark ? 'dark' : 'light';
  return palettes[me?.palette || 'viethealth'][mode];
}
