import { useCallback, useMemo, useState } from 'react';
import { Redirect, router, useFocusEffect } from 'expo-router';
import { ScrollView, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Copy, EmptyState, ErrorNote, Field, ListItem, Loading, Screen, SectionHeader } from '../../ui';
import type { WorkspacePage } from '../../workspace-types';

export default function Services() {
  const { me, request } = useSession(); const t = useTheme();
  const [menu, setMenu] = useState<WorkspacePage | null>(null); const [error, setError] = useState(''); const [query, setQuery] = useState('');
  useFocusEffect(useCallback(() => {
    let active = true; setError('');
    void request<WorkspacePage>('workspace/', { path: '/portal/', method: 'GET', menu_only: true }).then(value => { if (active) setMenu(value); })
      .catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [request]));
  const groups = useMemo(() => {
    const hidden = (path: string, label: string) => path.startsWith('/admin') || path.startsWith('/reports/') || path.startsWith('/portal/reports/')
      || ['/portal/finance/periods/', '/portal/finance/salaries/', '/portal/finance/dependents/', '/portal/finance/tax-config/',
        '/portal/hcns-forms/salary-scale/', '/portal/assets-admin/', '/portal/inventory/', '/portal/disposal/'].some(prefix => path.startsWith(prefix))
      || /trung tâm báo cáo|báo cáo.*excel|excel|chạy lương|lương cơ bản nv|người phụ thuộc|cấu hình thuế|thang bảng lương|quản lý tài sản|kiểm kê tài sản|thanh lý tài sản|nhập dữ liệu hàng loạt|xuất dữ liệu hàng loạt/i.test(label);
    const links = (menu?.navigation || []).filter(link => !hidden(link.path, link.label)
      && !['/portal/', '/portal/profile/', '/portal/organization-chart/', '/portal/profile/requests/'].includes(link.path)
      && link.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
    return [...new Set(links.map(link => link.group || 'Nghiệp vụ'))].map(name => ({ name, links: links.filter(link => (link.group || 'Nghiệp vụ') === name) }));
  }, [menu, query]);
  const iconForGroup = (group: string): React.ComponentProps<typeof Ionicons>['name'] => {
    if (/cá nhân|nhân viên/i.test(group)) return 'person-outline'; if (/nhân sự|hr/i.test(group)) return 'people-outline';
    if (/hành chính|tài sản|mua sắm/i.test(group)) return 'briefcase-outline'; if (/tài chính|lương/i.test(group)) return 'wallet-outline';
    if (/tra cứu|báo cáo/i.test(group)) return 'search-outline'; if (/phê duyệt|duyệt/i.test(group)) return 'checkmark-circle-outline'; return 'grid-outline';
  };
  const iconForLink = (label: string): React.ComponentProps<typeof Ionicons>['name'] => {
    if (/chấm công/i.test(label)) return 'time-outline'; if (/nghỉ phép|nghỉ/i.test(label)) return 'calendar-outline';
    if (/duyệt|phê duyệt/i.test(label)) return 'checkmark-done-outline'; if (/hồ sơ|nhân viên/i.test(label)) return 'person-outline';
    if (/tài sản|kiểm kê/i.test(label)) return 'cube-outline'; if (/phòng họp|đặt xe|văn phòng phẩm|mua sắm/i.test(label)) return 'briefcase-outline';
    if (/đào tạo|tuyển dụng/i.test(label)) return 'school-outline'; return 'document-text-outline';
  };
  if (!me) return <Redirect href="/login" />;
  return <Screen title="Nghiệp vụ" compact scrollable={false}>
    <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }} keyboardShouldPersistTaps="handled">
      <Field label="Tìm nghiệp vụ" placeholder="Ví dụ: chấm công, nghỉ phép" value={query} onChangeText={setQuery} autoCapitalize="none" />
      <View style={{ flexDirection: 'row', gap: 10, flexWrap: 'wrap' }}>
        <View style={{ flex: 1, minWidth: 155, borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Hồ sơ" icon="person-circle-outline" onPress={() => router.push('/account')} /></View>
        <View style={{ flex: 1, minWidth: 155, borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Cài đặt" icon="settings-outline" onPress={() => router.push('/settings')} /></View>
      </View>
      <View style={{ borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Hồ sơ chi tiết" subtitle="Thông tin và quá trình công tác" icon="person-outline" onPress={() => router.push('/personal-profile')} /></View>
      <View style={{ borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Sơ đồ tổ chức" icon="git-network-outline" onPress={() => router.push('/organization')} /></View>
      {me.can_request_profile_change ? <View style={{ borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Yêu cầu cập nhật hồ sơ" icon="create-outline" onPress={() => router.push('/profile-change')} /></View> : null}
      {me.can_approve_profile_change ? <View style={{ borderRadius: 14, backgroundColor: t.surface }}><ListItem title="Duyệt cập nhật hồ sơ" icon="checkmark-done-outline" onPress={() => router.push('/profile-approvals')} /></View> : null}
      {groups.map(group => <View key={group.name} style={{ gap: 6 }}>
        <SectionHeader title={group.name} icon={iconForGroup(group.name)} detail={`${group.links.length} mục`} />
        <View style={{ borderRadius: 14, backgroundColor: t.surface }}>
          {group.links.map((link, index) => <View key={`${link.path}-${index}`}>
            {index ? <View style={{ height: 1, marginLeft: 56, backgroundColor: t.cardBorder }} /> : null}
            <ListItem title={link.label} icon={iconForLink(link.label)} onPress={() => router.push({ pathname: '/workspace', params: { path: link.path } })} />
          </View>)}
        </View>
      </View>)}
      {error ? <ErrorNote message={error} /> : null}
      {!menu && !error ? <Loading /> : null}
      {menu && groups.length === 0 ? <EmptyState icon="search-outline" title="Không tìm thấy nghiệp vụ" description="Thử từ khóa khác hoặc xóa nội dung tìm kiếm." /> : null}
      <Copy muted>Danh mục thay đổi theo quyền của tài khoản.</Copy>
    </ScrollView>
  </Screen>;
}
