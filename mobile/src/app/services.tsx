import { useCallback, useState } from 'react';
import { Redirect, router, useFocusEffect } from 'expo-router';
import { useSession } from '../session';
import { Button, Card, Copy, ErrorNote, Loading, Screen } from '../ui';
import type { WorkspacePage } from '../workspace-types';

export default function Services() {
  const { me, request } = useSession();
  const [menu, setMenu] = useState<WorkspacePage | null>(null); const [error, setError] = useState('');
  useFocusEffect(useCallback(() => {
    let active = true; setError('');
    void request<WorkspacePage>('workspace/', { path: '/portal/', method: 'GET', menu_only: true }).then(value => { if (active) setMenu(value); })
      .catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [request]));
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Nghiệp vụ" description="Chức năng theo quyền tài khoản của bạn">
    <Button label="Quay lại hồ sơ" secondary onPress={() => router.back()} />
    <Card><Copy title>Cá nhân</Copy>
      <Button label="Hồ sơ chi tiết" secondary onPress={() => router.push('/personal-profile')} />
      <Button label="Sơ đồ tổ chức" secondary onPress={() => router.push('/organization')} />
      {me.can_request_profile_change ? <Button label="Yêu cầu cập nhật hồ sơ" secondary onPress={() => router.push('/profile-change')} /> : null}
    </Card>
    {me.can_approve_profile_change ? <Card><Copy title>Phê duyệt</Copy><Button label="Duyệt cập nhật hồ sơ" secondary onPress={() => router.push('/profile-approvals')} /></Card> : null}
    <ErrorNote message={error} />{!menu && !error ? <Loading /> : null}
    {[...new Set(menu?.navigation.map(link => link.group || 'Nghiệp vụ') || [])].map(group => <Card key={group}><Copy title>{group}</Copy>
      {menu?.navigation.filter(link => (link.group || 'Nghiệp vụ') === group && !['/portal/profile/', '/portal/organization-chart/', '/portal/profile/requests/'].includes(link.path)).map((link, index) =>
        <Button key={index} label={link.label} secondary onPress={() => router.push({ pathname: '/workspace', params: { path: link.path } })} />)}
    </Card>)}
  </Screen>;
}
