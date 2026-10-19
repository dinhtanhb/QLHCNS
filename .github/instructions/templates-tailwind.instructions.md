---
name: Django templates and shared UI
description: Giữ hợp đồng, trợ năng và thành phần giao diện IHRMS.
applyTo: 'src/templates/**/*.html,src/apps/**/templates/**/*.html,src/static/css/**/*.css,src/static/js/**/*.js'
---

Đọc [DESIGN.md](../../DESIGN.md) và [AGENTS.md](../../AGENTS.md).

- Dùng token `--ui-*` và thành phần chung; utility Tailwind bổ trợ theo cấu hình repo.
- Giữ CSRF/autoescape, tên và giá trị control, GET/POST, validation và quyền.
  Ẩn nút không thay thế guard phía server.
- Nhãn luôn hiện, focus rõ, bàn phím và native fallback hoạt động; nội dung dài
  không bị cắt để ép số hàng. Bảng hẹp cuộn trong vùng có tên truy cập được.
- Với CSS/form/bảng: browser QA bằng tài khoản giả trên DB/media cô lập, sáng/tối,
  rộng/hẹp; chạy layout audit, form contract và print UAT theo AGENTS.md.
- Bản in có hợp đồng riêng; kiểm ảnh PDF về màu, viền, ngắt trang và khoảng ký.
