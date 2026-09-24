import {
  H1, H2, H3, Text, Stack, Grid, Card, CardHeader, CardBody,
  Table, Pill, Row, Callout, Divider, useCanvasState,
} from "cursor/canvas";

const phases = [
  ["0 · Chốt phạm vi", "Bạn + chủ quy trình", "Xác nhận quy trình thật, người duyệt, dữ liệu và chính sách M365; ghi rõ quyết định."],
  ["1 · Nền tảng an toàn", "IT / nhà triển khai", "Bản mã có thể dựng lại; môi trường SIT; HTTPS, tài khoản dịch vụ, log và khôi phục được thử."],
  ["2 · SQL Server", "IT + DBA", "IHRMS kết nối database riêng; migrate sạch; smoke test và kiểm thử nghiệp vụ đạt trên SQL."],
  ["3 · Microsoft 365", "IT Entra admin + nhà triển khai", "SSO, email, SharePoint và Teams chạy trên tài khoản/site thử; quyền Graph tối thiểu và audit."],
  ["4 · UAT nghiệp vụ", "HR + Tài chính + quản lý + nhân viên", "Kịch bản thật bằng dữ liệu ẩn danh; ký xác nhận quyền, chấm công, nghỉ, lương, phiếu PDF."],
  ["5 · Pilot & go-live", "Bạn + IT + chủ nghiệp vụ", "Backup/restore và rollback diễn tập; nhóm pilot ký đạt; mở theo từng nhóm; có đầu mối hỗ trợ."],
];

const tasks = [
  ["Quy trình", "Chỉ định 1 người phụ trách HR, 1 Tài chính, 1 IT và người duyệt thay thế. Chốt ai được làm gì."],
  ["Microsoft 365", "Nhờ IT kiểm tra tenant Entra, app registration, admin consent, mailbox gửi hệ thống, SharePoint site/library và Teams channel."],
  ["Dữ liệu", "Chốt trường bắt buộc, quyền xem CCCD/lương, nơi lưu hồ sơ chính thức và thời hạn lưu."],
  ["Nghiệp vụ lương", "Tài chính xác nhận quy tắc và bảng đối chiếu mẫu; không chốt lương thật trước khi ký UAT."],
  ["Vận hành", "Chọn thời gian pilot, người hỗ trợ, cách báo sự cố, giờ bảo trì và người có quyền dừng go-live."],
];

const automations = [
  ["Thông báo tác nghiệp", "Có đơn nghỉ / duyệt / từ chối / task tới hạn", "Ghi trong IHRMS; gửi email; Teams chỉ báo nội dung tối thiểu và link an toàn.", "Người duyệt vẫn ra quyết định trong IHRMS."],
  ["Hợp đồng sắp hết hạn", "Job chạy mỗi ngày", "Nhắc HR ở mốc công ty chọn, ví dụ 60/30/7 ngày; không tự gia hạn.", "HR xác nhận danh sách và xử lý."],
  ["Nhắc chấm công/nghỉ", "Trước ngày chốt tháng", "Nhắc nhân viên hoàn tất; nhắc quản lý duyệt phần còn chờ.", "Quản lý kiểm tra; hệ thống không tự duyệt."],
  ["Tài liệu SharePoint", "Người dùng tải tài liệu", "Lưu tệp vào thư viện đúng quyền; SQL chỉ lưu metadata và ID/link; log kết quả.", "Không gửi hồ sơ nhạy cảm qua chat/email."],
  ["OneDrive", "Người dùng làm việc với tệp cá nhân", "Chỉ bật theo quyết định và mô hình quyền rõ; tránh dùng OneDrive cá nhân làm kho hồ sơ công ty.", "Chủ dữ liệu kiểm tra quyền chia sẻ."],
  ["Sao lưu & sức khỏe hệ thống", "Theo lịch IT", "SQL backup, backup tệp, kiểm tra dung lượng và báo khi job lỗi.", "IT diễn tập restore định kỳ; bản backup tách máy."],
];

const runSteps = [
  ["Tạo đơn / hồ sơ", "Người đề nghị nhập và gửi; hệ thống kiểm tra trường bắt buộc, ghi trạng thái và thông báo."],
  ["Duyệt", "Người đúng vai trò xem dữ liệu, duyệt hoặc từ chối kèm lý do; mọi hành động có lưu vết."],
  ["Thực hiện", "HR/Tài chính/Văn phòng xử lý hồ sơ đã duyệt; tệp chính thức nằm trong thư viện được công ty chỉ định."],
  ["Đối soát", "Chủ quy trình xác nhận kết quả; sai dữ liệu thì dùng luồng điều chỉnh, không sửa lén bản đã duyệt."],
  ["Đóng & lưu", "Hệ thống ghi trạng thái cuối; tài liệu có phân quyền; backup và retention theo chính sách công ty."],
];

export default function IhrmsRolloutCanvas() {
  const [view, setView] = useCanvasState("ihrms-rollout-view", "roadmap");
  const tabs = [
    ["roadmap", "Lộ trình"],
    ["admin", "Việc cần chốt"],
    ["automation", "Tự động hóa"],
    ["runbook", "Quy trình mẫu"],
  ];
  return (
    <Stack gap={18}>
      <Row justify="space-between" align="center" wrap>
        <Stack gap={4}>
          <H1>Kế hoạch đưa IHRMS vào vận hành</H1>
          <Text tone="secondary">Bản điều hành cho chủ dự án không chuyên kỹ thuật · Quy mô 30–50 người</Text>
        </Stack>
        <Pill active>Chưa qua cổng go-live</Pill>
      </Row>

      <Callout tone="warning" title="Điểm xuất phát hiện tại">
        Đặc tả kiến trúc nêu Entra ID, Outlook, Teams, SharePoint và OneDrive; mã nguồn đã rà soát chưa có các kết nối đó. Test 81 trường hợp đã chạy trên SQLite; cần kết quả riêng trên SQL Server và xác nhận tenant/quyền M365 trước go-live.
      </Callout>

      <Row gap={8} wrap>
        {tabs.map(([id, label]) => (
          <Pill key={id} active={view === id} onClick={() => setView(id)}>{label}</Pill>
        ))}
      </Row>

      {view === "roadmap" && (
        <Stack gap={12}>
          <H2>Sáu cổng kiểm soát — đi tuần tự</H2>
          <Text tone="secondary">Ước lượng thời gian chỉ lập sau khi IT và chủ nghiệp vụ xác nhận nguồn lực; không bỏ cổng vì đã cài được phần mềm.</Text>
          <Table headers={["Cổng", "Chủ trì", "Điều kiện để qua cổng"]} rows={phases} striped />
          <Grid columns={2} gap={12}>
            <Card>
              <CardHeader>Quy tắc dừng</CardHeader>
              <CardBody><Text>Không mở dữ liệu thật nếu còn lỗi phân quyền, chưa xác nhận công thức lương, chưa kiểm thử SQL Server, hoặc chưa khôi phục được bản backup trên môi trường thử.</Text></CardBody>
            </Card>
            <Card>
              <CardHeader>Cách triển khai phù hợp</CardHeader>
              <CardBody><Text>Pilot trước với HR, Tài chính và một bộ phận; sau khi chốt lỗi mới mở rộng toàn công ty. Giữ quy trình hiện tại làm phương án dự phòng trong pilot.</Text></CardBody>
            </Card>
          </Grid>
        </Stack>
      )}

      {view === "admin" && (
        <Stack gap={12}>
          <H2>Việc bạn có thể điều phối ngay</H2>
          <Text tone="secondary">Bạn không cần nhập cấu hình máy chủ. Hãy giao đúng người và yêu cầu bằng chứng hoàn thành.</Text>
          <Table headers={["Chủ đề", "Việc cần chốt / yêu cầu"]} rows={tasks} striped />
          <Callout tone="info" title="Thông tin không gửi trong chat">
            Không gửi mật khẩu, Client Secret, chuỗi kết nối SQL, khóa bí mật hoặc phiếu lương. IT lưu chúng trên máy chủ trong vùng cấu hình bảo mật.
          </Callout>
        </Stack>
      )}

      {view === "automation" && (
        <Stack gap={12}>
          <H2>Tự động hóa có kiểm soát</H2>
          <Text tone="secondary">Tự động nhắc và chuyển thông tin; không tự động phê duyệt nghỉ, sửa công hay khóa lương.</Text>
          <Table headers={["Luồng", "Khi nào chạy", "Hệ thống tự làm", "Người chịu trách nhiệm"]} rows={automations} striped />
          <H3>Thứ tự nên làm</H3>
          <Text>1) Email và nhắc hạn → 2) lưu tài liệu chính thức vào SharePoint → 3) thông báo Teams → 4) SSO Entra → 5) OneDrive nếu chính sách công ty xác định rõ đối tượng và quyền truy cập.</Text>
        </Stack>
      )}

      {view === "runbook" && (
        <Stack gap={12}>
          <H2>Quy trình chuẩn cho mỗi nghiệp vụ</H2>
          <Text tone="secondary">Áp dụng cho nghỉ phép, tuyển dụng, mua sắm, tài liệu và các yêu cầu cần duyệt.</Text>
          <Table headers={["Bước", "Cách vận hành"]} rows={runSteps} striped />
          <Divider />
          <H3>Đối soát bảng lương trước phát hành</H3>
          <Text>Tài chính chuẩn bị kỳ → kiểm tra công đã duyệt và cấu hình hiệu lực → tính → người thứ hai đối chiếu bảng mẫu → người có thẩm quyền khóa → phát hành PDF → xác nhận mỗi nhân viên chỉ xem được phiếu của mình.</Text>
          <Callout tone="warning" title="Riêng SQL Server Express">
            SQL Server 2022 Express giới hạn tối đa 10 GB mỗi database. IT cần theo dõi dung lượng và xác nhận phương án nâng edition nếu tăng trưởng vượt mức.
          </Callout>
        </Stack>
      )}

      <Divider />
      <Text size="small" tone="tertiary">Căn cứ: docs/00_Project_Charter.md, docs/02_Solution_Architecture.md, docs/08_Deployment_Standards.md, docs/10_RBAC_Permission_Matrix.md, docs/15_API_Contract_Specification.md và rà soát mã nguồn ngày 24/09/2026. Các đặc tả là mục tiêu cần triển khai/kiểm chứng, không phải bằng chứng connector hiện đã hoạt động.</Text>
    </Stack>
  );
}
