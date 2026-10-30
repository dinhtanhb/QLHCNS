import { useCallback, useRef, useState } from 'react';
import { RefreshControl, ScrollView, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Button, Card, Copy, EmptyState, ErrorNote, Screen, SectionHeader, Skeleton, StatusChip, dateLabel, s } from '../../ui';
import type { Attendance, Leave, Notice, Page } from '../../types';
import { useApprovalInbox } from '../../approval-inbox';

type Resource = 'attendance' | 'leaves' | 'approvals' | 'notices';
const resourceNames: Record<Resource, string> = { attendance: 'Chấm công', leaves: 'Nghỉ phép', approvals: 'Duyệt đơn', notices: 'Thông báo' };
// Copy only: keep this limit in sync with page() in src/apps/mobile/views.py
// (Paginator(queryset, 30)). When pagination changes, update these labels and Home UAT.
const RECENT_KPI_LIMIT = 30;

export default function Home() {
  const { me, request } = useSession(); const t = useTheme(); const canApprove = Boolean(me?.can_approve);
  const { count: approvalCount, updateCount } = useApprovalInbox();
  const [attendance, setAttendance] = useState<Page<Attendance> | null>(null); const [leaves, setLeaves] = useState<Page<Leave> | null>(null);
  const [approvals, setApprovals] = useState<Page<Leave> | null>(null); const [notices, setNotices] = useState<Page<Notice> | null>(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<Partial<Record<Resource, string>>>({});
  const [partLoading, setPartLoading] = useState<Partial<Record<Resource, boolean>>>({ attendance: true, leaves: true, approvals: true, notices: true });
  const sequence = useRef(0);
  const load = useCallback(async () => {
    const current = ++sequence.current;
    setLoading(true); setErrors({});
    setPartLoading({ attendance: true, leaves: true, approvals: canApprove, notices: true });
    const part = async <T,>(key: Resource, path: string, apply: (value: T) => void) => {
      try {
        const value = await request<T>(path);
        if (current === sequence.current) apply(value);
      } catch (e) {
        if (current === sequence.current) setErrors(previous => ({ ...previous, [key]: e instanceof Error ? e.message : 'Chưa tải được dữ liệu.' }));
      } finally {
        if (current === sequence.current) setPartLoading(previous => ({ ...previous, [key]: false }));
      }
    };
    await Promise.allSettled([
      part<Page<Attendance>>('attendance', 'attendance/', setAttendance),
      part<Page<Leave>>('leaves', 'leaves/', setLeaves),
      ...(canApprove ? [part<Page<Leave>>('approvals', 'approvals/', value => { setApprovals(value); updateCount(value.count); })] : []),
      part<Page<Notice>>('notices', 'notifications/', setNotices),
    ]);
    if (current === sequence.current) setLoading(false);
  }, [canApprove, request, updateCount]);
  useFocusEffect(useCallback(() => { void load(); return () => { sequence.current += 1; }; }, [load]));
  const name = me?.profile?.full_name?.trim() || me?.username || 'bạn';
  const firstName = name.split(/\s+/).slice(-1)[0];
  const recent = [...(leaves?.items || [])].slice(0, 2);
  const pendingMine = leaves?.items.filter(row => /pending|chờ/i.test(row.status)).length || 0;
  const pendingApprovals = approvals?.items.filter(row => /pending|chờ/i.test(row.status)).length || 0;
  const hours = attendance?.items.reduce((sum, row) => sum + (Number(row.hours) || 0), 0) || 0;
  const metrics = [
    { label: 'Bản ghi chấm công', value: String(attendance?.count ?? '—'), icon: 'calendar-outline' as const },
    { label: `Giờ làm (${RECENT_KPI_LIMIT} bản ghi gần nhất)`, value: attendance ? hours.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) : '—', icon: 'time-outline' as const },
    { label: `Đơn chờ (${RECENT_KPI_LIMIT} đơn gần nhất)`, value: leaves ? String(pendingMine) : '—', icon: 'document-text-outline' as const },
    ...(me?.can_approve ? [{ label: 'Cần duyệt', value: String(approvalCount ?? '—'), icon: 'checkmark-done-outline' as const }]
      : [{ label: `Chưa đọc (${RECENT_KPI_LIMIT} thông báo gần nhất)`, value: String(notices?.items.filter(row => !row.is_read).length ?? '—'), icon: 'notifications-outline' as const }]),
  ];
  return <Screen title="Trang chủ" compact scrollable={false}>
    <ScrollView contentContainerStyle={{ padding: 16, gap: 18 }} refreshControl={<RefreshControl refreshing={loading} onRefresh={() => void load()} />}>
      {Object.entries(errors).map(([key, message]) => <ErrorNote key={key} message={`${resourceNames[key as Resource]}: ${message}`} />)}
      {Object.keys(errors).length ? <Button label="Thử tải lại" variant="secondary" onPress={() => void load()} /> : null}
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
        <Card style={{ flex: 1, minHeight: 152, justifyContent: 'space-between' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}><Ionicons name={metric.icon} size={18} color={t.brand} /><View style={{ flex: 1 }}><Copy muted>{metric.label}</Copy></View></View>
          <Text allowFontScaling style={{ color: t.text, fontSize: 24, lineHeight: 30, fontWeight: '700' }}>{metric.value}</Text>
        </Card></View>)}</View>
      <Copy muted style={s.small}>{`Bản ghi chấm công${canApprove ? ' và Cần duyệt' : ''} tính trên toàn bộ dữ liệu. Các số ghi “gần nhất” chỉ tính trên ${RECENT_KPI_LIMIT} bản ghi mới nhất.`}</Copy>
      {me?.can_approve ? <View style={s.stack}>
        <SectionHeader title="Việc cần xử lý" action={<Button label="Tất cả" variant="text" onPress={() => router.push('/(tabs)/approvals')} />} />
        {partLoading.approvals && !approvals ? <Skeleton /> : null}
        {(approvals?.items || []).slice(0, 2).map(row => <Card key={row.id}><View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
          <Copy title>{row.employee_name}</Copy><StatusChip label="Chờ duyệt" tone="warning" /></View>
          <Copy>{row.leave_type} · {dateLabel(row.from_date)} – {dateLabel(row.to_date)}</Copy></Card>)}
        {!partLoading.approvals && !errors.approvals && approvals && pendingApprovals === 0 ? <EmptyState icon="checkmark-done-outline" title="Đã xử lý hết" description="Đơn mới sẽ xuất hiện tại đây." /> : null}
      </View> : null}
      <View style={s.stack}><SectionHeader title="Hoạt động gần đây" />
        {partLoading.leaves && !leaves ? <Skeleton /> : null}
        {recent.map(row => <Card key={row.id}><View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
          <Copy title>{row.leave_type}</Copy><StatusChip label={row.status_label} tone={/approved|duyệt/i.test(row.status) ? 'success' : /reject|từ chối/i.test(row.status) ? 'danger' : 'warning'} /></View>
          <Copy muted>{dateLabel(row.from_date)} – {dateLabel(row.to_date)} · {row.total_days} ngày</Copy></Card>)}
        {!partLoading.leaves && !errors.leaves && leaves && recent.length === 0 ? <EmptyState title="Chưa có hoạt động" description="Đơn nghỉ phép và cập nhật gần đây sẽ hiện ở đây." /> : null}
      </View>
      <Button label={`Thông báo${notices?.count ? ` · ${notices.count}` : ''}`} variant="text" icon="notifications-outline" onPress={() => router.push('/(tabs)/notifications')} />
    </ScrollView>
  </Screen>;
}
