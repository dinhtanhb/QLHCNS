import { Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, Screen, useRows } from '../ui';

type Person = { id: number; name: string; employee_code: string; department: string; position: string; manager_id: number | null; manager: string };
export default function Organization() {
  const { me } = useSession(); const rows = useRows<Person>('organization/');
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Sơ đồ tổ chức" description="Nhân viên đang làm việc và quan hệ quản lý">
    <Button label="Quay lại nghiệp vụ" secondary onPress={() => router.back()} />{rows.controls}
    {rows.data?.items.map(person => <Card key={person.id}><Copy title>{person.name}</Copy><Copy muted>{person.employee_code}</Copy>
      <Copy>{person.department} · {person.position}</Copy><Copy>Quản lý trực tiếp: {person.manager || 'Không có trong sơ đồ hiện tại'}</Copy></Card>)}
    {rows.data?.count === 0 ? <Copy>Chưa có nhân viên đang làm việc.</Copy> : null}
  </Screen>;
}
