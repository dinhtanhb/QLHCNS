import { Platform } from 'react-native';
import { Directory, File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as Print from 'expo-print';
import type { NativeDocument } from './api';

const folder = () => new Directory(Paths.cache, 'ihrms-workspace');

export function discardWorkspaceFile(uri: string) {
  if (Platform.OS === 'web') return;
  try { const file = new File(uri); if (file.exists) file.delete(); } catch { /* Cache cleanup retries on the next session. */ }
}

export async function clearWorkspaceFiles() {
  if (Platform.OS === 'web') return;
  try { const directory = folder(); if (directory.exists) directory.delete(); } catch { /* OS cache cleanup can retry on next login. */ }
}

export async function receiveDocument(document: NativeDocument) {
  try {
    if (Platform.OS === 'web') {
      const blob = await document.response.blob();
      const uri = URL.createObjectURL(blob);
      const link = window.document.createElement('a'); link.href = uri; link.download = document.name; link.click();
      setTimeout(() => URL.revokeObjectURL(uri), 60000);
      return null;
    }
    const directory = folder(); directory.create({ idempotent: true, intermediates: true });
    const file = new File(directory, `${Date.now()}-${Math.random().toString(16).slice(2)}-${document.name}`);
    file.create({ overwrite: true });
    try {
      if (document.response.body) await document.response.body.pipeTo(file.writableStream());
      else file.write(new Uint8Array(await document.response.arrayBuffer()));
      return file.uri;
    } catch (error) { if (file.exists) file.delete(); throw error; }
  } finally { document.cancel(); }
}

export async function openDocument(uri: string, mimeType: string) {
  if (mimeType.startsWith('text/html')) {
    const html = await new File(uri).text();
    const result = await Print.printToFileAsync({ html, width: 595.28, height: 841.89 });
    const pdf = new File(result.uri);
    const target = new File(folder(), `${Date.now()}-IHRMS.pdf`);
    pdf.move(target);
    uri = target.uri; mimeType = 'application/pdf';
  }
  if (!(await Sharing.isAvailableAsync())) throw new Error('Thiết bị chưa hỗ trợ mở hoặc chia sẻ tệp này.');
  await Sharing.shareAsync(uri, { mimeType, dialogTitle: 'Mở hoặc lưu tài liệu IHRMS' });
}
