export type WorkspaceLink = { kind: 'link'; label: string; path: string; external: boolean; group?: string };
export type WorkspaceField = {
  id: string; name: string; type: string; label: string; value: string | string[];
  options: { label: string; value: string; disabled: boolean; selected: boolean }[];
  checked: boolean; disabled: boolean; readonly: boolean; required: boolean; multiple: boolean;
  placeholder: string; maxLength: number | null; min: string | null; max: string | null; step: string | null; accept: string;
  numericLocale: boolean;
  remote: string | null;
  reference?: string | null; referenceKey?: string | null;
};
export type WorkspaceAction = { label: string; name: string; value: string; path: string; method: string; confirm: string; print?: boolean };
export type WorkspaceForm = { kind: 'form'; id: string; path: string; fields: WorkspaceField[]; templates: Record<string, WorkspaceField[]>; repeat?: WorkspaceField[]; references?: Record<string, Record<string, Record<string, unknown>>>; actions: WorkspaceAction[]; blocks: WorkspaceBlock[]; format?: 'json' };
export type WorkspaceBlock = WorkspaceLink | WorkspaceForm | { kind: 'heading' | 'text' | 'notice'; text: string } | { kind: 'print'; label: string; path: string } |
  { kind: 'table'; rows: { cells: { label: string; text: string }[]; blocks: WorkspaceBlock[] }[] };
export type WorkspacePage = { kind: 'page'; path: string; title: string; blocks: WorkspaceBlock[]; navigation: WorkspaceLink[]; messages: { text: string; level: number }[] };
export type WorkspaceJSON = { kind: 'json'; path: string; data: unknown; messages: { text: string; level: number }[] };
export type WorkspacePayload = { path: string; method: string; fields?: string[][]; uploads?: { name: string; key: string }[]; print?: boolean; json?: unknown };
