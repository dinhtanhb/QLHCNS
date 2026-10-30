import { useState } from 'react';
import { FlatList, RefreshControl, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Copy, EmptyState, ErrorNote, Screen, Skeleton, StatusChip, dateLabel, useRows } from '../../ui';
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
      if (row.destination === 'leaves') router.push('/(tabs)/my-work?section=leave');
      else if (row.destination === 'approvals' && me?.can_approve) router.push('/(tabs)/approvals');
      else if (row.destination === 'profile-requests') router.push('/profile-change');
      else if (row.destination === 'workspace' && row.path) router.push({ pathname: '/workspace', params: { path: row.path } });
      else await rows.reload();
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể mở thông báo.'); }
    finally { setBusy(false); }
  };
  return <Screen title="Thông báo" compact scrollable={false}>
    {error || rows.error ? <View style={{ paddingHorizontal: 16, gap: 8 }}>
      <ErrorNote message={error || rows.error} />
      {rows.error ? <Button label="Thử tải lại" variant="secondary" onPress={() => void rows.reload()} /> : null}
    </View> : null}
    <FlatList data={rows.data?.items || []} keyExtractor={row => String(row.id)} contentContainerStyle={{ padding: 16, gap: 10, flexGrow: 1 }}
      refreshControl={<RefreshControl refreshing={rows.loading} onRefresh={() => void rows.reload()} />}
      onEndReached={rows.loadMore} onEndReachedThreshold={0.4}
      ListEmptyComponent={rows.loading ? <Skeleton /> : rows.error ? undefined : <EmptyState icon="notifications-outline" title="Chưa có thông báo" description="Thông tin mới sẽ xuất hiện tại đây." />}
      ListFooterComponent={rows.loadingMore ? <Copy muted>Đang tải thêm…</Copy> : undefined}
      renderItem={({ item }) => <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
          <View style={{ flex: 1, minWidth: 180 }}><Copy title>{item.title}</Copy></View>
          {!item.is_read ? <StatusChip label="Mới" tone="info" /> : null}
        </View>
        <Copy>{item.message}</Copy><Copy muted>{dateLabel(item.created_at)}</Copy>
        {!item.is_read || item.destination ? <Button label="Mở" variant="text" icon="arrow-forward" disabled={busy} accessibilityLabel={`Mở thông báo: ${item.title}`} onPress={() => void open(item)} /> : null}
      </Card>} />
  </Screen>;
}
