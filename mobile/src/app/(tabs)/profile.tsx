import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { useSession } from '../../session';
import { Button, Card, Confirm, Copy, ErrorNote, Screen } from '../../ui';
import type { LeaveOptions } from '../../types';
import { enablePush, pushConfigured } from '../../push';

export default function Profile() {
  const { me, busy, error, logout, request } = useSession();
  const [options, setOptions] = useState<LeaveOptions | null>(null);
  const [confirm, setConfirm] = useState(false); const [loadError, setLoadError] = useState('');
  const [pushMessage, setPushMessage] = useState('');
  const [pushBusy, setPushBusy] = useState(false);
  useFocusEffect(useCallback(() => { setOptions(null); setLoadError('');
    void request<LeaveOptions>('leave-options/').then(setOptions).catch(e => setLoadError(e.message));
  }, [request]));
  return <Screen title="Hồ sơ của tôi" description="Thông tin cá nhân và quỹ nghỉ phép">
    <ErrorNote message={error || loadError} />
    <Button label="Cài đặt" onPress={() => router.push('/settings')} secondary />
    <Button label="Nghiệp vụ" onPress={() => router.push('/services')} secondary />
    {me?.profile ? <Card><Copy title>{me.profile.full_name}</Copy><Copy muted>{me.profile.employee_code} · {me.profile.position}</Copy>
      <Copy>{me.profile.department}</Copy><Copy>{me.profile.company_email || 'Chưa có email công ty'}</Copy></Card>
      : <Card><Copy>Tài khoản chưa được gắn hồ sơ nhân viên. Vui lòng liên hệ Nhân sự.</Copy></Card>}
    {options ? <Card><Copy title>Phép năm {options.year}</Copy><Copy>{options.annual_available === null ? 'Chưa được cấp hạn mức phép năm.' : `${options.annual_available} ngày còn có thể đăng ký`}</Copy>
      <Copy muted>Đã tính các đơn đang chờ duyệt.</Copy></Card> : null}
    {me?.can_manage_hr ? <Card><Copy title>Dành cho Nhân sự</Copy><Copy>Đợt đầu hỗ trợ theo dõi và duyệt nghỉ phép theo quyền. Quản trị hồ sơ, hạn mức và cấu hình tiếp tục thực hiện trên cổng web.</Copy></Card> : null}
    <Copy muted>Tài khoản: {me?.username}</Copy>
    <Button label="Đăng xuất" onPress={() => setConfirm(true)} secondary busy={busy} />
    {pushConfigured ? <Card><Copy title>Thông báo trên điện thoại</Copy><Copy muted>Sau khi cấp quyền, ứng dụng tự đăng ký lại khi mở hoặc trở về. Lời nhắc chỉ hiển thị chung; mở ứng dụng để xem nội dung.</Copy>
      <Button label="Bật thông báo trên điện thoại" secondary busy={pushBusy} onPress={() => {
        setPushBusy(true); setPushMessage('');
        void enablePush().then(token => request('push-token/', { token })).then(() => setPushMessage('Đã bật thông báo trên thiết bị này.'))
          .catch(e => setPushMessage(e.message)).finally(() => setPushBusy(false));
      }} />{pushMessage ? <Copy>{pushMessage}</Copy> : null}</Card> : null}
    {confirm ? <Confirm title="Đăng xuất IHRMS?" detail="Phiên đăng nhập trên thiết bị này sẽ kết thúc."
      busy={busy} onCancel={() => setConfirm(false)} onConfirm={() => { void logout().catch(() => setConfirm(false)); }} /> : null}
  </Screen>;
}
