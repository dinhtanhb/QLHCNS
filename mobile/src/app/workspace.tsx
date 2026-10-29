import { useCallback, useRef, useState } from 'react';
import { Alert, Linking, Modal, Platform, ScrollView, View } from 'react-native';
import { Redirect, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Loading, Screen, s } from '../ui';
import { useTheme } from '../theme';
import { Blocks, JSONResults, type PickedUpload } from '../workspace-renderer';
import type { WorkspaceJSON, WorkspacePage, WorkspacePayload } from '../workspace-types';
import type { NativeDocument } from '../api';
import { discardWorkspaceFile, openDocument, receiveDocument } from '../workspace-files';

export default function Workspace() {
  const { me, request, refreshMe } = useSession(); const t = useTheme();
  const params = useLocalSearchParams<{ path?: string }>();
  const path = typeof params.path === 'string' ? params.path : '/portal/';
  const [page, setPage] = useState<WorkspacePage | WorkspaceJSON | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [version, setVersion] = useState(0);
  const [menu, setMenu] = useState(false); const [document, setDocument] = useState<{ uri: string; name: string; contentType: string } | null>(null);
  const [notice, setNotice] = useState('');
  const sequence = useRef(0); const activeDocument = useRef<NativeDocument | null>(null);
  const posting = useRef(false);
  const submit = useCallback(async (payload: WorkspacePayload, uploads: PickedUpload[] = []) => {
    if (posting.current) return;
    if (payload.method === 'POST') posting.current = true;
    const current = ++sequence.current; setBusy(true); setError(''); setNotice('');
    try {
      let body: unknown = payload;
      if (uploads.length) {
        const form = new FormData(); payload.uploads = [];
        for (const [index, upload] of uploads.entries()) {
          const key = 'upload_'+index; payload.uploads.push({ key, name: upload.name });
          if (Platform.OS === 'web' && upload.file.file) form.append(key, upload.file.file, upload.file.name);
          else Reflect.apply(form.append, form, [key, { uri: upload.file.uri, name: upload.file.name, type: upload.file.mimeType || 'application/octet-stream' }]);
        }
        form.append('payload', JSON.stringify(payload)); body = form;
      }
      const result = await request<WorkspacePage | WorkspaceJSON | NativeDocument>('workspace/', body);
      if (current !== sequence.current) { if (result.kind === 'file') result.cancel(); return; }
      if (result.kind === 'file') {
        activeDocument.current = result;
        let uri: string | null;
        try { uri = await receiveDocument(result); }
        catch { throw new Error('Không tải được tệp. Kiểm tra mạng và dung lượng rồi thử lại.'); }
        finally { activeDocument.current = null; }
        if (current !== sequence.current) { if (uri) discardWorkspaceFile(uri); return; }
        if (uri) setDocument({ uri, name: result.name, contentType: result.contentType });
        setNotice(Platform.OS === 'web' ? 'Đã tải tệp.' : 'Tệp đã sẵn sàng. Chọn Mở hoặc lưu tệp để sử dụng.');
      } else {
        setPage(result); setVersion(value => value+1); setDocument(null);
      }
      if (payload.method === 'POST') await refreshMe();
    } catch (e) {
      if (current === sequence.current) setError(e instanceof Error ? e.message : 'Chưa xử lý được nghiệp vụ.');
      throw e;
    } finally { if (payload.method === 'POST') posting.current = false; if (current === sequence.current) setBusy(false); }
  }, [refreshMe, request]);
  useFocusEffect(useCallback(() => {
    setPage(null); setDocument(null); setError(''); setNotice('');
    if (!me?.username) return;
    void submit({ path, method: 'GET' }).catch(() => undefined);
    return () => { sequence.current += 1; activeDocument.current?.cancel(); activeDocument.current = null; };
  }, [path, submit, me?.username]));
  const navigate = (target: string, external = false) => {
    if (external || /^(https?:|mailto:|tel:)/i.test(target)) {
      if (!/^(https?:|mailto:|tel:)/i.test(target)) return;
      Alert.alert('Mở ứng dụng bên ngoài?', target, [{ text: 'Quay lại', style: 'cancel' }, { text: 'Mở', onPress: () => { void Linking.openURL(target).catch(() => setError('Chưa mở được liên kết này.')); } }]);
      return;
    }
    setMenu(false);
    if (target === page?.path) void submit({ path: target, method: 'GET' }).catch(() => undefined);
    else router.push({ pathname: '/workspace', params: { path: target } });
  };
  if (!me) return <Redirect href="/login" />;
  const actions = { busy, navigate, submit };
  return <Screen title={page?.kind === 'page' ? page.title : 'Nghiệp vụ IHRMS'}>
    <View style={s.row}><Button label="Quay lại" secondary onPress={() => router.canGoBack() ? router.back() : router.replace('/services')} disabled={busy} />
      <Button label="Tải lại" secondary busy={busy} onPress={() => { void submit({ path: page?.path || path, method: 'GET' }).catch(() => undefined); }} />
      {page?.kind === 'page' && page.navigation.length ? <Button label="Danh mục nghiệp vụ" secondary onPress={() => setMenu(true)} /> : null}</View>
    <ErrorNote message={error} />{notice ? <Copy>{notice}</Copy> : null}{busy ? <Loading /> : null}
    {document ? <Card><Copy>{document.name}</Copy><Copy muted>Tệp lưu tạm trong ứng dụng và được dọn khi đăng xuất hoặc mở lại app.</Copy>
      <Button label="Mở hoặc lưu tệp" secondary onPress={() => { void openDocument(document.uri, document.contentType).catch(() => setError('Chưa mở được tệp. Vui lòng thử lại.')); }} /></Card> : null}
    {page?.messages.map((message, index) => message.level >= 40 ? <ErrorNote key={index} message={message.text} /> : <Copy key={index}>{message.text}</Copy>)}
    {page?.kind === 'page' ? <Blocks key={version} blocks={page.blocks} actions={actions} /> : page?.kind === 'json' ? <JSONResults data={page.data} actions={actions} /> : null}
    <Modal visible={menu} transparent onRequestClose={() => setMenu(false)}><View style={[s.overlay, { backgroundColor: t.bg }]}>
      <Button label="Đóng danh mục" secondary onPress={() => setMenu(false)} /><ScrollView contentContainerStyle={s.stack}>
        {page?.kind === 'page' ? page.navigation.map((item, index) => <Button key={index} label={item.label} secondary onPress={() => navigate(item.path, item.external)} />) : null}
      </ScrollView></View></Modal>
  </Screen>;
}
