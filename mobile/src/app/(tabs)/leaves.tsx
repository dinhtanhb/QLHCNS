import { router, useLocalSearchParams } from 'expo-router';
import { Button, Card, Copy, Screen, dateLabel, useRows } from '../../ui';
import type { Leave } from '../../types';
import { useSession } from '../../session';

export default function LeavesScreen() {
  const rows = useRows<Leave>('leaves/'); const { me } = useSession();
  const { submitted } = useLocalSearchParams<{ submitted?: string }>();
  return <Screen title="Nghỉ phép" description="Đơn của bạn và nhân viên thuộc phạm vi quản lý">
    {submitted ? <Card><Copy>Đã gửi đơn xin nghỉ phép, chờ phê duyệt.</Copy></Card> : null}
    {me?.profile ? <Button label="Tạo đơn nghỉ phép" onPress={() => router.push('/leave-new')} /> : null}
    {rows.controls}{rows.data?.items.map(row => <Card key={row.id}><Copy title>{row.leave_type} · {row.status_label}</Copy>
      <Copy>{dateLabel(row.from_date)} – {dateLabel(row.to_date)} · {row.total_days} ngày</Copy>
      <Copy muted>{row.employee_name}</Copy>{row.reason ? <Copy>{row.reason}</Copy> : null}</Card>)}
    {rows.data?.count === 0 ? <Card><Copy>Chưa có đơn nghỉ phép.</Copy></Card> : null}
  </Screen>;
}
