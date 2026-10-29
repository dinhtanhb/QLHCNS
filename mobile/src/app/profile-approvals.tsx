import { useState } from 'react';
import { Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Confirm, Copy, ErrorNote, Field, Screen, useRows } from '../ui';

type Item = { id: number; employee_name: string; field_label: string; old_value: string; new_value: string; reason: string; has_attachment: boolean };
type Decision = 'approve' | 'reject' | 'more_info';
const actions = [{ value: 'approve', label: 'Duyệt' }, { value: 'reject', label: 'Từ chối' }, { value: 'more_info', label: 'Yêu cầu bổ sung' }] as const;
export default function ProfileApprovals() {
  const { me, request } = useSession(); const rows = useRows<Item>('profile-approvals/');
  const [selected, setSelected] = useState<{ item: Item; decision: Decision; label: string } | null>(null);
  const [note, setNote] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  if (!me) return <Redirect href="/login" />;
  if (!me.can_approve_profile_change) return <Screen title="Duyệt cập nhật hồ sơ"><Copy>Bạn không có quyền xử lý yêu cầu này.</Copy></Screen>;
  return <Screen title="Duyệt cập nhật hồ sơ" description="Các yêu cầu đang chờ Nhân sự xử lý">
    <Button label="Quay lại nghiệp vụ" secondary onPress={() => router.back()} />{rows.controls}
    <ErrorNote message={error} />{message ? <Copy>{message}</Copy> : null}
    {rows.data?.items.map(item => <Card key={item.id}><Copy title>{item.employee_name} · {item.field_label}</Copy>
      <Copy>Hiện tại: {item.old_value || 'Chưa có'}</Copy><Copy>Đề nghị: {item.new_value}</Copy><Copy muted>Lý do: {item.reason || 'Không ghi'}</Copy>
      {item.has_attachment ? <Copy muted>Có chứng từ đính kèm. Xem chứng từ trên cổng web trước khi xử lý.</Copy> : null}
      {actions.map(action => <Button key={action.value} label={`${action.label} yêu cầu #${item.id}`} secondary disabled={busy} onPress={() => {
        setSelected({ item, decision: action.value, label: action.label }); setNote(''); setError(''); setMessage('');
      }} />)}</Card>)}
    {rows.data?.count === 0 ? <Copy>Không có yêu cầu đang chờ xử lý.</Copy> : null}
    {selected ? <Confirm title={`${selected.label} yêu cầu #${selected.item.id}?`} detail={`${selected.item.employee_name} · ${selected.item.field_label}: ${selected.item.new_value}`}
        busy={busy} onCancel={() => setSelected(null)} onConfirm={() => {
          setBusy(true);
          void request(`profile-requests/${selected.item.id}/decision/`, { decision: selected.decision, note })
            .then(() => { setSelected(null); setMessage('Đã xử lý yêu cầu cập nhật hồ sơ.'); void rows.reload(); })
            .catch(e => { setSelected(null); setError(e.message); }).finally(() => setBusy(false));
        }}><Field label="Ý kiến xử lý" value={note} onChangeText={setNote} maxLength={500} editable={!busy} /></Confirm> : null}
  </Screen>;
}
