import { useState } from 'react';
import { router } from 'expo-router';
import { Button, Card, Copy, ErrorNote, Screen, dateLabel, useRows } from '../../ui';
import type { Notice } from '../../types';
import { useSession } from '../../session';

export default function NotificationsScreen() {
  const rows = useRows<Notice>('notifications/'); const { request, me } = useSession();
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const open = async (row: Notice) => {
    if (busy) return;
    setBusy(true); setError('');
    try {
      await request(`notifications/${row.id}/read/`, {});
      if (row.destination === 'leaves') router.push('/(tabs)/leaves');
      else if (row.destination === 'approvals' && me?.can_approve) router.push('/(tabs)/approvals');
      else if (row.destination === 'profile-requests') router.push('/profile-change');
      else await rows.reload();
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể mở thông báo.'); }
    finally { setBusy(false); }
  };
  return <Screen title="Thông báo" description="Cập nhật dành riêng cho bạn">
    {rows.controls}<ErrorNote message={error} />
    {rows.data?.items.map(row => <Card key={row.id}><Copy title>{row.title}</Copy><Copy>{row.message}</Copy>
      <Copy muted>{dateLabel(row.created_at)} · {row.is_read ? 'Đã đọc' : 'Chưa đọc'}</Copy>
      {!row.is_read || row.destination ? <Button label={`Mở thông báo #${row.id}`} secondary disabled={busy} onPress={() => void open(row)} /> : null}</Card>)}
    {rows.data?.count === 0 ? <Card><Copy>Bạn chưa có thông báo.</Copy></Card> : null}
  </Screen>;
}
