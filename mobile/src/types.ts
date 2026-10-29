export type Palette = 'viethealth' | 'chamdong' | 'thanam';
export type Me = {
  username: string; role: string; can_approve: boolean; can_manage_hr: boolean; can_request_profile_change: boolean; palette: Palette;
  profile: null | { employee_code: string; full_name: string; department: string; position: string; company_email: string; join_date: string; personal_email: string; mobile_phone: string; address: string };
};
export type Page<T> = { items: T[]; page: number; count: number; has_next: boolean };
export type Leave = { id: number; employee_name: string; leave_type: string; from_date: string; to_date: string; total_days: string; reason: string; status: string; status_label: string };
export type Attendance = { id: number; date: string; check_in: string | null; check_out: string | null; hours: string | null; status_label: string };
export type Notice = { id: number; title: string; message: string; is_read: boolean; created_at: string; destination: 'approvals' | 'leaves' | null };
export type LeaveOptions = { types: { id: number; leave_type_name: string }[]; year: number; annual_available: string | null; can_submit: boolean };
