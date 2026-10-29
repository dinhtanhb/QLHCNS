import { Redirect, router } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, Screen } from '../ui';

export default function Services() {
  const { me } = useSession();
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Nghiệp vụ" description="Chức năng theo quyền tài khoản của bạn">
    <Button label="Quay lại hồ sơ" secondary onPress={() => router.back()} />
    <Card><Copy title>Cá nhân</Copy>
      <Button label="Hồ sơ chi tiết" secondary onPress={() => router.push('/personal-profile')} />
      <Button label="Sơ đồ tổ chức" secondary onPress={() => router.push('/organization')} />
      {me.can_request_profile_change ? <Button label="Yêu cầu cập nhật hồ sơ" secondary onPress={() => router.push('/profile-change')} /> : null}
    </Card>
    {me.can_approve_profile_change ? <Card><Copy title>Phê duyệt</Copy><Button label="Duyệt cập nhật hồ sơ" secondary onPress={() => router.push('/profile-approvals')} /></Card> : null}
  </Screen>;
}
