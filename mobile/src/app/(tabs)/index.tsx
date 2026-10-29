import { useCallback, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Pressable, Text, View } from 'react-native';
import { useSession } from '../../session';
import { useTheme } from '../../theme';
import { Button, Card, Copy, ErrorNote, Loading, Screen, s } from '../../ui';
import type { Attendance, Leave, LeaveOptions, Notice, Page } from '../../types';

type Metric = { key: string; label: string; value: string; icon: React.ComponentProps<typeof Ionicons>['name']; hint: string; action: () => void };

export default function Home() {
  const { me, request } = useSession(); const t = useTheme();
  const [metrics, setMetrics] = useState<Metric[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const [attendanceDays, setAttendanceDays] = useState<Attendance[]>([]);
  useFocusEffect(useCallback(() => {
    let active = true; setLoading(true); setError('');
    void (async () => {
      // Native sessions update an idle-activity marker on each request. Keep these
      // reads sequential so concurrent session saves cannot invalidate one another.
      const attendance = await request<Page<Attendance>>('attendance/').catch(() => null);
      const leaves = await request<Page<Leave>>('leaves/').catch(() => null);
      const approvals = me?.can_approve ? await request<Page<Leave>>('approvals/').catch(() => null) : null;
      const notices = await request<Page<Notice>>('notifications/').catch(() => null);
      const leaveOptions = await request<LeaveOptions>('leave-options/').catch(() => null);
      if (!active) return;
      const pending = leaves?.items.filter(row => row.status.toLowerCase() === 'pending').length ?? 0;
      const unread = notices?.items.filter(row => !row.is_read).length ?? 0;
      const hours = attendance?.items.reduce((total, row) => total + (Number(row.hours) || 0), 0) ?? 0;
      setAttendanceDays(attendance?.items.slice(0, 7).reverse() ?? []);
      const values: Metric[] = [
        { key: 'attendance', label: 'Bản ghi chấm công', value: String(attendance?.count ?? '—'), icon: 'calendar-outline', hint: `${hours.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} giờ trong 30 bản ghi mới nhất`, action: () => router.push('/(tabs)/attendance') },
        { key: 'leave', label: 'Đơn nghỉ chờ duyệt', value: String(pending), icon: 'time-outline', hint: leaveOptions?.annual_available === null || leaveOptions?.annual_available === undefined ? 'Xem các đơn nghỉ của bạn' : `Còn ${leaveOptions.annual_available} ngày phép`, action: () => router.push('/(tabs)/leaves') },
        ...(me?.can_approve ? [{ key: 'approval', label: 'Đơn cần xử lý', value: String(approvals?.count ?? '—'), icon: 'checkmark-done-outline' as const, hint: 'Danh sách chờ duyệt theo quyền', action: () => router.push('/(tabs)/approvals') }] : []),
        { key: 'notice', label: 'Thông báo chưa đọc', value: String(unread), icon: 'notifications-outline', hint: 'Cập nhật mới trong ứng dụng', action: () => router.push('/(tabs)/notifications') },
      ];
      setMetrics(values); setError([attendance, leaves, notices].every(value => value === null) ? 'Chưa tải được số liệu. Hãy kiểm tra kết nối rồi thử tải lại.' : '');
    })().finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [request, me?.can_approve]));

  return <Screen title="Trang chủ" description="Số liệu cá nhân và công việc mới nhất của bạn.">
    <ErrorNote message={error} />
    {!loading && attendanceDays.length === 1 ? <Card><Copy title>Chấm công gần nhất</Copy>
      <Copy>{attendanceDays[0].hours === null ? 'Chưa có số giờ' : `${Number(attendanceDays[0].hours).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} giờ`} · {attendanceDays[0].date.slice(8, 10)}/{attendanceDays[0].date.slice(5, 7)}</Copy>
    </Card> : null}
    {!loading && attendanceDays.length > 1 ? <Card><Copy title>Giờ làm việc · 7 bản ghi gần nhất</Copy>
      <View accessibilityLabel="Biểu đồ số giờ làm việc theo ngày" style={[s.row, { alignItems: 'flex-end', flexWrap: 'nowrap', height: 150, justifyContent: 'space-around' }]}>
        {attendanceDays.map(row => {
          const hours = Math.max(0, Number(row.hours) || 0); const maxHours = Math.max(...attendanceDays.map(day => Number(day.hours) || 0), 1);
          const height = Math.max(8, Math.round((hours / maxHours) * 96));
          return <View key={row.id} style={{ flex: 1, alignItems: 'center', justifyContent: 'flex-end', height: '100%', gap: 4 }}>
            <Copy muted>{hours.toLocaleString('vi-VN', { maximumFractionDigits: 1 })}h</Copy>
            <View style={{ height, width: 24, maxWidth: '80%', backgroundColor: t.brand, borderRadius: 4 }} />
            <Copy muted>{row.date.slice(8, 10)}/{row.date.slice(5, 7)}</Copy>
          </View>;
        })}
      </View></Card> : null}
    {loading ? <Loading /> : <View style={[s.row, { alignItems: 'stretch' }]}>{metrics.map(metric =>
      <View key={metric.key} style={{ width: '47%', minWidth: 145, flexGrow: 1 }}><Pressable accessibilityRole="button" accessibilityLabel={`Mở ${metric.label.toLocaleLowerCase()}`}
        onPress={metric.action} style={({ pressed }) => [s.card, { backgroundColor: t.surface, borderColor: t.cardBorder, opacity: pressed ? 0.75 : 1 }]}>
        <View style={[s.row, { gap: 8 }]}><Ionicons name={metric.icon} size={20} color={t.brand} /><Copy muted>{metric.label}</Copy></View>
        <Text style={{ fontSize: 24, lineHeight: 32, fontWeight: '600', color: t.text }}>{metric.value}</Text>
        <Copy muted>{metric.hint}</Copy>
      </Pressable></View>
    )}</View>}
    <Card><Copy title>Truy cập nhanh</Copy>
      <Button label="Nghiệp vụ" secondary onPress={() => router.push('/services')} />
      <Button label="Cài đặt tài khoản" secondary onPress={() => router.push('/settings')} />
    </Card>
  </Screen>;
}
