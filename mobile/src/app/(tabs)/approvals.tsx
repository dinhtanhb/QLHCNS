import { useState } from 'react';
import { Redirect } from 'expo-router';
import { Button, Card, Confirm, Copy, ErrorNote, Screen, dateLabel, useRows } from '../../ui';
import type { Leave } from '../../types';
import { useSession } from '../../session';

export default function ApprovalsScreen() {
  const { me, request } = useSession();
  const rows = useRows<Leave>('approvals/');
  const [choice, setChoice] = useState<{ row: Leave; decision: string } | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  if (!me?.can_approve) return <Redirect href="/(tabs)" />;
  const decide = async () => {
    if (!choice || busy) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await request(`leaves/${choice.row.id}/decision/`, { decision: choice.decision });
      setChoice(null); setMessage('Đã xử lý đơn nghỉ phép.'); await rows.reload();
    } catch (err) { setChoice(null); setError(err instanceof Error ? err.message : 'Không thể xử lý đơn.'); await rows.reload(); }
    finally { setBusy(false); }
  };
  return <Screen title="Duyệt đơn" description="Các đơn chờ xử lý trong phạm vi được cấp quyền">
    {rows.controls}<ErrorNote message={error} />{message ? <Card><Copy>{message}</Copy></Card> : null}
    {rows.data?.items.map(row => <Card key={row.id}><Copy title>{row.employee_name}</Copy><Copy>{row.leave_type} · {row.total_days} ngày</Copy>
      <Copy>{dateLabel(row.from_date)} – {dateLabel(row.to_date)}</Copy>{row.reason ? <Copy muted>{row.reason}</Copy> : null}
      <Button label={`Duyệt đơn #${row.id}`} onPress={() => setChoice({ row, decision: 'Approved' })} disabled={busy} />
      <Button label={`Từ chối đơn #${row.id}`} secondary onPress={() => setChoice({ row, decision: 'Rejected' })} disabled={busy} /></Card>)}
    {rows.data?.count === 0 ? <Card><Copy>Không có đơn chờ duyệt.</Copy></Card> : null}
    {choice ? <Confirm title={choice.decision === 'Approved' ? 'Duyệt đơn nghỉ phép?' : 'Từ chối đơn nghỉ phép?'}
      detail={`${choice.row.employee_name} · ${dateLabel(choice.row.from_date)} – ${dateLabel(choice.row.to_date)}`}
      busy={busy} onConfirm={() => void decide()} onCancel={() => setChoice(null)} /> : null}
  </Screen>;
}
