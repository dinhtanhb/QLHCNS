import { useState } from 'react';
import { FlatList, RefreshControl, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Card, Copy, EmptyState, ErrorNote, Screen, SegmentedControl, Skeleton, StatusChip, dateLabel, useRows } from '../../ui';
import type { Attendance, Leave } from '../../types';

type WorkRow = Leave | Attendance;
const isLeave = (row: WorkRow): row is Leave => 'leave_type' in row;

export default function MyWork() {
  const params = useLocalSearchParams<{ section?: string; submitted?: string }>();
  const [section, setSection] = useState<'leave' | 'attendance'>(params.section === 'attendance' ? 'attendance' : 'leave');
  const rows = useRows<WorkRow>(section === 'leave' ? 'leaves/' : 'attendance/');
  return <Screen title="Việc của tôi" compact scrollable={false}>
    <View style={{ paddingHorizontal: 16, paddingTop: 8, gap: 12 }}>
      {params.submitted ? <Card><Copy>Đã gửi đơn xin nghỉ phép, chờ phê duyệt.</Copy></Card> : null}
      <SegmentedControl label="Loại công việc" value={section} onChange={setSection} options={[{ value: 'leave', label: 'Nghỉ phép' }, { value: 'attendance', label: 'Chấm công' }]} />
      {section === 'leave' ? <Button label="Tạo đơn nghỉ phép" icon="add-circle-outline" onPress={() => router.push('/leave-new')} /> : null}
      <ErrorNote message={rows.error} />
    </View>
    <FlatList data={rows.data?.items || []} keyExtractor={item => `${section}-${item.id}`}
      contentContainerStyle={{ padding: 16, paddingTop: 8, gap: 10, flexGrow: 1 }}
      refreshControl={<RefreshControl refreshing={rows.loading} onRefresh={() => void rows.reload()} />}
      onEndReached={rows.loadMore} onEndReachedThreshold={0.45}
      ListEmptyComponent={rows.loading ? <Skeleton /> : <EmptyState icon={section === 'leave' ? 'calendar-outline' : 'time-outline'}
        title={section === 'leave' ? 'Chưa có đơn nghỉ phép' : 'Chưa có dữ liệu chấm công'}
        description={section === 'leave' ? 'Các đơn đã gửi sẽ xuất hiện tại đây.' : 'Bản ghi chấm công mới nhất sẽ xuất hiện tại đây.'}
        action={section === 'leave' ? { label: 'Tạo đơn nghỉ phép', onPress: () => router.push('/leave-new') } : undefined} />}
      ListFooterComponent={rows.loadingMore ? <Copy muted>Đang tải thêm…</Copy> : undefined}
      renderItem={({ item }) => <Card>
        {isLeave(item) ? <>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
            <Copy title>{item.leave_type}</Copy><StatusChip label={item.status_label} tone={/duyệt|approved/i.test(item.status) ? 'success' : /từ chối|rejected/i.test(item.status) ? 'danger' : 'warning'} />
          </View>
          <Copy>{dateLabel(item.from_date)} – {dateLabel(item.to_date)} · {item.total_days} ngày</Copy>
          {item.reason ? <Copy muted>{item.reason}</Copy> : null}
        </> : <>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
            <Copy title>{dateLabel(item.date)}</Copy><StatusChip label={item.status_label || 'Đã ghi nhận'} tone="success" />
          </View>
          <Copy>Vào {item.check_in?.slice(0, 5) || '—'} · Ra {item.check_out?.slice(0, 5) || '—'}</Copy>
          <Copy muted>{item.hours === null ? 'Chưa có số giờ' : `${item.hours} giờ làm việc`}</Copy>
        </>}
      </Card>} />
  </Screen>;
}
