"""Generate/check mobile color roles from the approved web token source."""
import argparse
import json
from pathlib import Path

from check_ui_contrast import palette_blocks, resolve, ratio

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'mobile/src/palettes.json'
ROLES = {'bg': '--ui-bg', 'surface': '--ui-surface', 'text': '--ui-text',
    'muted': '--ui-text-muted', 'brand': '--ui-brand', 'onBrand': '--ui-on-brand',
    'border': '--ui-border', 'cardBorder': '--ui-card-border',
    'danger': '--ui-danger-text', 'dangerBg': '--ui-danger-bg',
    'success': '--ui-success-text', 'successBg': '--ui-success-bg',
    'warning': '--ui-warning-text', 'warningBg': '--ui-warning-bg',
    'info': '--ui-info-text', 'infoBg': '--ui-info-bg'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = {palette: {mode: {name: resolve(values, token) for name, token in ROLES.items()}
            for mode, values in modes.items() if mode in ('light', 'dark')}
            for palette, modes in palette_blocks().items()}
    pairs = 0
    for modes in data.values():
        for t in modes.values():
            for fg, bg in [('text', 'bg'), ('text', 'surface'), ('muted', 'surface'),
                           ('muted', 'bg'), ('brand', 'surface'), ('onBrand', 'brand'),
                           ('danger', 'dangerBg'), ('success', 'successBg'),
                           ('warning', 'warningBg'), ('info', 'infoBg')]:
                assert ratio(t[fg], t[bg]) >= 4.5, (fg, bg, t)
                pairs += 1
            assert ratio(t['border'], t['surface']) >= 3
            pairs += 1
    expected = json.dumps(data, ensure_ascii=False, indent=2)+'\n'
    if args.check:
        assert DEST.read_text(encoding='utf-8') == expected, 'Mobile tokens differ; run ops/sync_mobile_tokens.py'
    else:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_text(expected, encoding='utf-8')
    print(f'3 palettes x 2 modes; {pairs} contrast checks OK; mobile tokens match web')


if __name__ == '__main__':
    main()
