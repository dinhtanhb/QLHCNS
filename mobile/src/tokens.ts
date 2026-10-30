/** Shared mobile sizes. Colors always come from the active server palette. */
export { default as palettes } from './palettes.json';
export const space = { x1: 4, x2: 8, x3: 12, x4: 16, x6: 24, x8: 32 } as const;
export const type = { caption: 12, label: 14, body: 16, title: 18, section: 20, page: 24, stat: 32 } as const;
export const radius = { control: 12, card: 16, panel: 20, pill: 999 } as const;
export const motion = { feedback: 120, panel: 180 } as const;
