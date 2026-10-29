import { useState } from 'react';
import { FlatList, RefreshControl, View } from 'react-native';
import { Redirect } from 'expo-router';
import { Button, Card, Confirm, Copy, EmptyState, ErrorNote, Screen, Skeleton, StatusChip, dateLabel, useRows } from '../../ui';
import type { Leave } from '../../types';
import { useSession } from '../../session';

export default function ApprovalsScreen() {
  const { me, request } = useSession(); const rows = useRows<Leave>('approvals/');
  const [choice, setChoice] = useState<{ row: Leave; decision: string } | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  if (!me?.can_approve) return <Redirect href="/(tabs)" />;
  const decide = async () => {
    if (!choice || busy) return;
    setBusy(true); setError(''); setMessage('');
    try { await request(`leaves/${choice.row.id}/decision/`, { decision: choice.decision }); setChoice(null); setMessage('Đã xử lý đơn nghỉ phép.'); await rows.reload(); }
    catch (err) { setChoice(null); setError(err instanceof Error ? err.message : 'Không thể xử lý đơn.'); await rows.reload(); }
    finally { setBusy(false); }
  };
  return <Screen title="Duyệt" compact scrollable={false}>
    <ErrorNote message={error || rows.error} />
    {message ? <Copy>{message}</Copy> : null}
    <FlatList data={rows.data?.items || []} keyExtractor={row => String(row.id)} contentContainerStyle={{ padding: 16, gap: 10, flexGrow: 1 }}
      refreshControl={<RefreshControl refreshing={rows.loading} onRefresh={() => void rows.reload()} />}
      onEndReached={rows.loadMore} onEndReachedThreshold={0.4}
      ListEmptyComponent={rows.loading ? <Skeleton /> : <EmptyState icon="checkmark-done-outline" title="Không có đơn cần duyệt" description="Đơn trong phạm vi bạn phụ trách sẽ hiện ở đây." />}
      ListFooterComponent={rows.loadingMore ? <Copy muted>Đang tải thêm…</Copy> : undefined}
      renderItem={({ item }) => <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}><Copy title>{item.employee_name}</Copy><StatusChip label="Chờ duyệt" tone="warning" /></View>
        <Copy>{item.leave_type} · {item.total_days} ngày</Copy><Copy muted>{dateLabel(item.from_date)} – {dateLabel(item.to_date)}</Copy>
        {item.reason ? <Copy>{item.reason}</Copy> : null}
        <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
          <View style={{ flex: 1, minWidth: 130 }}><Button label="Duyệt" accessibilityLabel={`Duyệt đơn của ${item.employee_name} ${dateLabel(item.from_date)}`} icon="checkmark" onPress={() => setChoice({ row: item, decision: 'Approved' })} disabled={busy} /></View>
          <View style={{ flex: 1, minWidth: 130 }}><Button label="Từ chối" accessibilityLabel={`Từ chối đơn của ${item.employee_name} ${dateLabel(item.from_date)}`} icon="close" variant="secondary" onPress={() => setChoice({ row: item, decision: 'Rejected' })} disabled={busy} /></View>
        </View>
      </Card>} />
    {choice ? <Confirm title={choice.decision === 'Approved' ? 'Duyệt đơn nghỉ phép?' : 'Từ chối đơn nghỉ phép?'}
      detail={`${choice.row.employee_name} · ${dateLabel(choice.row.from_date)} – ${dateLabel(choice.row.to_date)}`}
      busy={busy} onConfirm={() => void decide()} onCancel={() => setChoice(null)} /> : null}
  </Screen>;
}
