import { useEffect, useState } from 'react';
import { FlatList, Modal, RefreshControl, ScrollView, View, useWindowDimensions } from 'react-native';
import { Redirect } from 'expo-router';
import { AppBar, Button, Card, Confirm, Copy, EmptyState, ErrorNote, Screen, Skeleton, StatusChip, dateLabel, s, useRows } from '../../ui';
import type { Leave } from '../../types';
import { useSession } from '../../session';
import { useApprovalInbox } from '../../approval-inbox';
import { useTheme } from '../../theme';
import { radius, space } from '../../tokens';
import { approvalNeedsDetails } from '../../input-utils';

export default function ApprovalsScreen() {
  const { me, request } = useSession(); const rows = useRows<Leave>('approvals/');
  const t = useTheme(); const [details, setDetails] = useState<Leave | null>(null);
  const { fontScale } = useWindowDimensions();
  const { updateCount, refreshCount } = useApprovalInbox();
  useEffect(() => { if (rows.data) updateCount(rows.data.count); }, [rows.data, updateCount]);
  const [choice, setChoice] = useState<{ row: Leave; decision: string } | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  if (!me?.can_approve) return <Redirect href="/(tabs)" />;
  const decide = async () => {
    if (!choice || busy) return;
    setBusy(true); setError(''); setMessage('');
    try { await request(`leaves/${choice.row.id}/decision/`, { decision: choice.decision }); setChoice(null); setMessage('Đã xử lý đơn nghỉ phép.'); await Promise.allSettled([rows.reload(), refreshCount()]); }
    catch (err) { setChoice(null); setError(err instanceof Error ? err.message : 'Không thể xử lý đơn.'); await Promise.allSettled([rows.reload(), refreshCount()]); }
    finally { setBusy(false); }
  };
  return <Screen title="Duyệt" compact scrollable={false}>
    {error || rows.error || message ? <View style={{ paddingHorizontal: 16, gap: 8 }}>
      <ErrorNote message={error || rows.error} />
      {rows.error ? <Button label="Thử tải lại" variant="secondary" onPress={() => void rows.reload()} /> : null}
      {message ? <Copy>{message}</Copy> : null}
    </View> : null}
    <FlatList data={rows.data?.items || []} keyExtractor={row => String(row.id)} contentContainerStyle={{ padding: 16, gap: 10, flexGrow: 1 }}
      refreshControl={<RefreshControl refreshing={rows.loading} onRefresh={() => void rows.reload()} />}
      onEndReached={rows.loadMore} onEndReachedThreshold={0.4}
      ListEmptyComponent={rows.loading ? <Skeleton /> : rows.error ? undefined : <EmptyState icon="checkmark-done-outline" title="Không có đơn cần duyệt" description="Đơn trong phạm vi bạn phụ trách sẽ hiện ở đây." />}
      ListFooterComponent={rows.loadingMore ? <Copy muted>Đang tải thêm…</Copy> : undefined}
      renderItem={({ item }) => <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8 }}><Copy title numberOfLines={2} ellipsizeMode="tail" style={{ flex: 1 }}>{item.employee_name}</Copy><StatusChip label="Chờ duyệt" tone="warning" /></View>
        <Copy>{item.leave_type} · {item.total_days} ngày</Copy><Copy muted>{dateLabel(item.from_date)} – {dateLabel(item.to_date)}</Copy>
        {item.reason ? <Copy numberOfLines={3} ellipsizeMode="tail">{item.reason}</Copy> : null}
        {approvalNeedsDetails(item.employee_name, item.reason, fontScale) ? <Button label="Xem thêm" accessibilityLabel="Xem đầy đủ đơn nghỉ phép" variant="text" onPress={() => setDetails(item)} /> : null}
        <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
          <View style={{ flex: 1, minWidth: 130 }}><Button label="Duyệt" accessibilityLabel={`Duyệt đơn của ${item.employee_name} ${dateLabel(item.from_date)}`} icon="checkmark" onPress={() => setChoice({ row: item, decision: 'Approved' })} disabled={busy} /></View>
          <View style={{ flex: 1, minWidth: 130 }}><Button label="Từ chối" accessibilityLabel={`Từ chối đơn của ${item.employee_name} ${dateLabel(item.from_date)}`} icon="close" variant="secondary" onPress={() => setChoice({ row: item, decision: 'Rejected' })} disabled={busy} /></View>
        </View>
      </Card>} />
    <Modal visible={details !== null} transparent animationType="slide" onRequestClose={() => setDetails(null)}>
      <View style={[s.overlay, { justifyContent: 'flex-end', padding: 0, backgroundColor: t.overlay }]}>
        <View style={{ maxHeight: '90%', backgroundColor: t.bg, borderTopLeftRadius: radius.panel, borderTopRightRadius: radius.panel }}>
          <AppBar title="Chi tiết đơn nghỉ phép" action={<Button label="Đóng chi tiết" variant="text" onPress={() => setDetails(null)} />} />
          <ScrollView contentContainerStyle={{ padding: space.x4, gap: space.x3 }}>
            <Copy title>{details?.employee_name}</Copy>
            <Copy>{details?.leave_type} · {details?.total_days} ngày</Copy>
            <Copy muted>{details ? `${dateLabel(details.from_date)} – ${dateLabel(details.to_date)}` : ''}</Copy>
            <Copy>{details?.reason || 'Không có lý do bổ sung.'}</Copy>
          </ScrollView>
        </View>
      </View>
    </Modal>
    {choice ? <Confirm title={choice.decision === 'Approved' ? 'Duyệt đơn nghỉ phép?' : 'Từ chối đơn nghỉ phép?'}
      detail={`${choice.row.employee_name} · ${dateLabel(choice.row.from_date)} – ${dateLabel(choice.row.to_date)}`}
      busy={busy} onConfirm={() => void decide()} onCancel={() => setChoice(null)} /> : null}
  </Screen>;
}
