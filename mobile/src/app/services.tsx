import { useCallback, useMemo, useState } from 'react';
import { Redirect, router, useFocusEffect } from 'expo-router';
import { Pressable, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../session';
import { useTheme } from '../theme';
import { Button, Card, Copy, ErrorNote, Loading, Screen, s } from '../ui';
import type { WorkspacePage } from '../workspace-types';

export default function Services() {
  const { me, request } = useSession(); const t = useTheme();
  const [menu, setMenu] = useState<WorkspacePage | null>(null); const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<string[]>([]);
  useFocusEffect(useCallback(() => {
    let active = true; setError('');
    void request<WorkspacePage>('workspace/', { path: '/portal/', method: 'GET', menu_only: true }).then(value => { if (active) setMenu(value); })
      .catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [request]));
  const groups = useMemo(() => {
    const hidden = (path: string, label: string) => path.startsWith('/admin') || path.startsWith('/reports/')
      || path.startsWith('/portal/reports/')
      || ['/portal/finance/periods/', '/portal/finance/salaries/', '/portal/finance/dependents/',
        '/portal/finance/tax-config/', '/portal/hcns-forms/salary-scale/', '/portal/assets-admin/',
        '/portal/inventory/', '/portal/disposal/'].some(prefix => path.startsWith(prefix))
      || /trung tâm báo cáo|báo cáo.*excel|excel|chạy lương|lương cơ bản nv|người phụ thuộc|cấu hình thuế|thang bảng lương|quản lý tài sản|kiểm kê tài sản|thanh lý tài sản|nhập dữ liệu hàng loạt|xuất dữ liệu hàng loạt/i.test(label);
    const links = (menu?.navigation || []).filter(link => !hidden(link.path, link.label)
      && !['/portal/', '/portal/profile/', '/portal/organization-chart/', '/portal/profile/requests/'].includes(link.path));
    return [...new Set(links.map(link => link.group || 'Nghiệp vụ'))].map(name => ({ name, links: links.filter(link => (link.group || 'Nghiệp vụ') === name) }));
  }, [menu]);
  const iconForGroup = (group: string): React.ComponentProps<typeof Ionicons>['name'] => {
    if (/cá nhân|nhân viên/i.test(group)) return 'person-outline';
    if (/nhân sự|hr/i.test(group)) return 'people-outline';
    if (/hành chính|tài sản|mua sắm/i.test(group)) return 'briefcase-outline';
    if (/tài chính|lương/i.test(group)) return 'wallet-outline';
    if (/tra cứu|báo cáo/i.test(group)) return 'search-outline';
    if (/phê duyệt|duyệt/i.test(group)) return 'checkmark-circle-outline';
    return 'grid-outline';
  };
  const iconForLink = (label: string): React.ComponentProps<typeof Ionicons>['name'] => {
    if (/chấm công/i.test(label)) return 'time-outline';
    if (/nghỉ phép|nghỉ/i.test(label)) return 'calendar-outline';
    if (/duyệt|phê duyệt/i.test(label)) return 'checkmark-done-outline';
    if (/hồ sơ|nhân viên/i.test(label)) return 'person-outline';
    if (/tài sản|kiểm kê/i.test(label)) return 'cube-outline';
    if (/phòng họp|đặt xe|văn phòng phẩm|mua sắm/i.test(label)) return 'briefcase-outline';
    if (/đào tạo|tuyển dụng/i.test(label)) return 'school-outline';
    return 'document-text-outline';
  };
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Nghiệp vụ" description="Chức năng theo quyền tài khoản của bạn">
    <Button label="Quay lại trang chủ" secondary onPress={() => router.push('/(tabs)')} />
    <Card><Copy muted>Các mục được hiển thị theo quyền tài khoản và ưu tiên thao tác nhanh trên điện thoại.</Copy></Card>
    <Card><View style={[s.row, { gap: 8 }]}><Ionicons name="person-circle-outline" size={22} color={t.brand} /><Copy title>Hồ sơ cá nhân</Copy></View>
      <Button label="Hồ sơ chi tiết" secondary onPress={() => router.push('/personal-profile')} />
      <Button label="Sơ đồ tổ chức" secondary onPress={() => router.push('/organization')} />
      {me.can_request_profile_change ? <Button label="Yêu cầu cập nhật hồ sơ" secondary onPress={() => router.push('/profile-change')} /> : null}
      {me.can_approve_profile_change ? <Button label="Duyệt cập nhật hồ sơ" secondary onPress={() => router.push('/profile-approvals')} /> : null}
    </Card>
    {groups.map(group => {
      const isOpen = expanded.includes(group.name);
      return <Card key={group.name}><Pressable accessibilityRole="button" accessibilityState={{ expanded: isOpen }} accessibilityLabel={`${group.name}, ${group.links.length} mục`}
        onPress={() => setExpanded(current => isOpen ? current.filter(name => name !== group.name) : [...current, group.name])}
        style={[s.row, { minHeight: 44, justifyContent: 'space-between' }]}>
        <View style={[s.row, { flex: 1 }]}><Ionicons name={iconForGroup(group.name)} size={22} color={t.brand} />
          <Copy title>{group.name}</Copy><Copy muted>({group.links.length})</Copy></View>
        <Ionicons name={isOpen ? 'chevron-up-outline' : 'chevron-down-outline'} size={20} color={t.muted} />
      </Pressable>
      {isOpen ? group.links.map((link, index) => <Pressable key={`${link.path}-${index}`} accessibilityRole="button" accessibilityLabel={link.label}
        onPress={() => router.push({ pathname: '/workspace', params: { path: link.path } })}
        style={[s.row, { minHeight: 48, borderTopWidth: 1, borderTopColor: t.cardBorder, paddingVertical: 8 }]}>
        <Ionicons name={iconForLink(link.label)} size={20} color={t.muted} /><View style={{ flex: 1 }}><Copy>{link.label}</Copy></View>
        <Ionicons name="chevron-forward-outline" size={18} color={t.muted} />
      </Pressable>) : null}</Card>;
    })}
    <ErrorNote message={error} />{!menu && !error ? <Loading /> : null}
  </Screen>;
}
