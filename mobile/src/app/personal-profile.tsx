import { useCallback, useState } from 'react';
import { useFocusEffect, Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Screen, dateLabel, moneyLabel, useRows } from '../ui';

type Details = {
  profile: null | { full_name: string; employee_code: string; date_of_birth: string; gender: string; department: string; position: string; manager: string;
    company_email: string; personal_email: string; mobile_phone: string; address: string; join_date: string; employment_status: string };
  salary: null | { basic: string; effective_date: string };
  contract: null | { number: string; type: string; start_date: string; end_date: string | null };
};
type History = { id: number; date: string; description: string; amount: string | null };
const kinds = [{ key: 'transfers', label: 'Điều chuyển' }, { key: 'promotions', label: 'Bổ nhiệm' }, { key: 'rewards', label: 'Khen thưởng' }, { key: 'disciplines', label: 'Kỷ luật' }] as const;

export default function PersonalProfile() {
  const { me, request } = useSession();
  const [details, setDetails] = useState<Details | null>(null); const [error, setError] = useState('');
  const [kind, setKind] = useState('transfers');
  const rows = useRows<History>(`profile-history/?kind=${kind}`);
  useFocusEffect(useCallback(() => {
    let active = true; setDetails(null); setError('');
    void request<Details>('my-profile/').then(value => { if (active) setDetails(value); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [request]));
  if (!me) return <Redirect href="/login" />;
  const p = details?.profile;
  return <Screen title="Hồ sơ chi tiết" description="Thông tin cá nhân và quá trình công tác của bạn">
    <Button label="Quay lại nghiệp vụ" secondary onPress={() => router.back()} /><ErrorNote message={error} />
    {p ? <Card><Copy title>{p.full_name}</Copy><Copy muted>{p.employee_code}</Copy>
      <Copy>Ngày sinh: {dateLabel(p.date_of_birth)} · {p.gender}</Copy><Copy>{p.department} · {p.position}</Copy>
      <Copy>Quản lý trực tiếp: {p.manager || 'Chưa có'}</Copy><Copy>Email công ty: {p.company_email || 'Chưa có'}</Copy>
      <Copy>Email cá nhân: {p.personal_email || 'Chưa có'}</Copy><Copy>Điện thoại: {p.mobile_phone || 'Chưa có'}</Copy>
      <Copy>Địa chỉ: {p.address || 'Chưa có'}</Copy><Copy>Ngày vào làm: {dateLabel(p.join_date)}</Copy><Copy>{p.employment_status}</Copy></Card> : details ? <Card><Copy>Tài khoản chưa gắn hồ sơ nhân viên.</Copy></Card> : null}
    {details?.salary ? <Card><Copy title>Lương cơ bản hiện tại</Copy><Copy>{moneyLabel(details.salary.basic)} đồng</Copy><Copy muted>Áp dụng từ {dateLabel(details.salary.effective_date)}</Copy></Card> : null}
    {details?.contract ? <Card><Copy title>Hợp đồng hiện tại</Copy><Copy>{details.contract.number} · {details.contract.type}</Copy>
      <Copy>Từ {dateLabel(details.contract.start_date)}</Copy><Copy>Đến {details.contract.end_date ? dateLabel(details.contract.end_date) : 'Không xác định thời hạn'}</Copy></Card> : null}
    {p ? <><Copy title>Quá trình công tác</Copy>{kinds.map(item => <Button key={item.key} label={`${kind === item.key ? '✓ ' : ''}${item.label}`} secondary onPress={() => setKind(item.key)} />)}
      {rows.controls}{rows.data?.items.map(row => <Card key={row.id}><Copy>{dateLabel(row.date)}</Copy><Copy>{row.description}</Copy>{row.amount !== null ? <Copy>{moneyLabel(row.amount)} đồng</Copy> : null}</Card>)}
      {rows.data?.count === 0 ? <Copy muted>Chưa có bản ghi trong mục này.</Copy> : null}</> : null}
  </Screen>;
}
