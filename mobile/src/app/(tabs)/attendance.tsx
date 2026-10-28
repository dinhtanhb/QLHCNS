import { Card, Copy, Screen, dateLabel, useRows } from '../../ui';
import type { Attendance } from '../../types';

export default function AttendanceScreen() {
  const rows = useRows<Attendance>('attendance/');
  return <Screen title="Chấm công" description="Dữ liệu chấm công cá nhân, mới nhất trước">
    {rows.controls}{rows.data?.items.map(row => <Card key={row.id}><Copy title>{dateLabel(row.date)} · {row.status_label}</Copy>
      <Copy>Vào {row.check_in?.slice(0, 5) || '—'} · Ra {row.check_out?.slice(0, 5) || '—'}</Copy>
      <Copy muted>{row.hours === null ? 'Chưa có số giờ' : `${row.hours} giờ làm việc`}</Copy></Card>)}
    {rows.data?.count === 0 ? <Card><Copy>Chưa có dữ liệu chấm công.</Copy></Card> : null}
  </Screen>;
}
