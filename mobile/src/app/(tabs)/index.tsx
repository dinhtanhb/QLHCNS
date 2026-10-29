import { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Button, Card, Copy, EmptyState, ErrorNote, Screen, SectionHeader, StatusChip, dateLabel, s } from '../../ui';
import type { Attendance, Leave, Notice, Page } from '../../types';

export default function Home() {
  const { me, request } = useSession(); const t = useTheme(); const canApprove = Boolean(me?.can_approve);
  const [attendance, setAttendance] = useState<Page<Attendance> | null>(null); const [leaves, setLeaves] = useState<Page<Leave> | null>(null);
  const [approvals, setApprovals] = useState<Page<Leave> | null>(null); const [notices, setNotices] = useState<Page<Notice> | null>(null);
  const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const a = await request<Page<Attendance>>('attendance/'); setAttendance(a);
      const l = await request<Page<Leave>>('leaves/'); setLeaves(l);
      const p = canApprove ? await request<Page<Leave>>('approvals/') : null; setApprovals(p);
      const n = await request<Page<Notice>>('notifications/'); setNotices(n);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chưa tải được dữ liệu.'); }
    finally { setLoading(false); }
  }, [canApprove, request]);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  const name = me?.profile?.full_name?.trim() || me?.username || 'bạn';
  const firstName = name.split(/\s+/).slice(-1)[0];
  const recent = [...(leaves?.items || [])].slice(0, 2);
  const pendingMine = leaves?.items.filter(row => /pending|chờ/i.test(row.status)).length || 0;
  const pendingApprovals = approvals?.items.filter(row => /pending|chờ/i.test(row.status)).length || 0;
  const hours = attendance?.items.reduce((sum, row) => sum + (Number(row.hours) || 0), 0) || 0;
  const metrics = [
    { label: 'Ngày công', value: String(attendance?.count ?? '—'), icon: 'calendar-outline' as const },
    { label: 'Giờ gần đây', value: hours.toLocaleString('vi-VN', { maximumFractionDigits: 1 }), icon: 'time-outline' as const },
    { label: 'Đơn chờ', value: String(pendingMine), icon: 'document-text-outline' as const },
    ...(me?.can_approve ? [{ label: 'Cần duyệt', value: String(approvals?.count ?? 0), icon: 'checkmark-done-outline' as const }]
      : [{ label: 'Chưa đọc', value: String(notices?.items.filter(row => !row.is_read).length ?? 0), icon: 'notifications-outline' as const }]),
  ];
  return <Screen title="Trang chủ" compact scrollable={false}>
    <ScrollView contentContainerStyle={{ padding: 16, gap: 18 }} refreshControl={<RefreshControl refreshing={loading} onRefresh={() => void load()} />}>
      <ErrorNote message={error} />
      <View style={[s.row, { flexWrap: 'nowrap', alignItems: 'center' }]}>
        <View accessibilityLabel={`Ảnh đại diện ${name}`} style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: t.brand, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color: t.onBrand, fontSize: 20, fontWeight: '700' }}>{firstName.slice(0, 1).toLocaleUpperCase()}</Text>
        </View>
        <View accessibilityLabel={`Tên nhân viên: ${name}`} style={{ flex: 1, minWidth: 0 }}><Copy muted>Xin chào</Copy>
          <Text numberOfLines={2} ellipsizeMode="tail" allowFontScaling style={{ color: t.text, fontSize: 18, lineHeight: 25, fontWeight: '600' }}>{name}</Text>
          <Copy muted>{me?.profile?.department || me?.role || 'IHRMS'}</Copy></View>
      </View>
      <View style={[s.row, { alignItems: 'stretch' }]}>
        <View style={{ flex: 1, minWidth: 150 }}><Button label="Tạo đơn nghỉ" icon="add-circle-outline" onPress={() => router.push('/leave-new')} /></View>
        <View style={{ flex: 1, minWidth: 150 }}><Button label="Xem chấm công" icon="time-outline" variant="secondary" onPress={() => router.push('/(tabs)/my-work?section=attendance')} /></View>
      </View>
      <View style={[s.row, { alignItems: 'stretch', gap: 10 }]}>{metrics.map(metric => <View key={metric.label} style={{ width: '47%', flexGrow: 1 }}>
        <Card style={{ minHeight: 112, justifyContent: 'space-between' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}><Ionicons name={metric.icon} size={18} color={t.brand} /><View style={{ flex: 1 }}><Copy muted>{metric.label}</Copy></View></View>
          <Text allowFontScaling style={{ color: t.text, fontSize: 24, lineHeight: 30, fontWeight: '700' }}>{metric.value}</Text>
        </Card></View>)}</View>
      {me?.can_approve ? <View style={s.stack}>
        <SectionHeader title="Việc cần xử lý" action={<Button label="Tất cả" variant="text" onPress={() => router.push('/(tabs)/approvals')} />} />
        {(approvals?.items || []).slice(0, 2).map(row => <Card key={row.id}><View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
          <Copy title>{row.employee_name}</Copy><StatusChip label="Chờ duyệt" tone="warning" /></View>
          <Copy>{row.leave_type} · {dateLabel(row.from_date)} – {dateLabel(row.to_date)}</Copy></Card>)}
        {!loading && pendingApprovals === 0 ? <EmptyState icon="checkmark-done-outline" title="Đã xử lý hết" description="Đơn mới sẽ xuất hiện tại đây." /> : null}
      </View> : null}
      <View style={s.stack}><SectionHeader title="Hoạt động gần đây" />
        {recent.map(row => <Card key={row.id}><View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
          <Copy title>{row.leave_type}</Copy><StatusChip label={row.status_label} tone={/approved|duyệt/i.test(row.status) ? 'success' : /reject|từ chối/i.test(row.status) ? 'danger' : 'warning'} /></View>
          <Copy muted>{dateLabel(row.from_date)} – {dateLabel(row.to_date)} · {row.total_days} ngày</Copy></Card>)}
        {!loading && recent.length === 0 ? <EmptyState title="Chưa có hoạt động" description="Đơn nghỉ phép và cập nhật gần đây sẽ hiện ở đây." /> : null}
      </View>
      <Button label={`Thông báo${notices?.count ? ` · ${notices.count}` : ''}`} variant="text" icon="notifications-outline" onPress={() => router.push('/(tabs)/notifications')} />
    </ScrollView>
  </Screen>;
}
