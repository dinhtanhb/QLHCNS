# Nhật ký diễn tập Restore — QLHCNS / IHRMS

Ghi lại mỗi lần diễn tập restore (bắt buộc hàng quý theo
docs/08_Deployment_Standards.md mục 21). Copy khối bên dưới, điền thông tin,
thêm vào đầu file (mới nhất lên trên).

---

## Quý ___ / Năm ____ — Ngày thực hiện: __ / __ / ____

- **Người thực hiện:**
- **Bản backup dùng test:** (tên file .bak, thời điểm tạo)
- **Log backup đi kèm (nếu có):** (tên file .trn, khoảng thời gian)
- **Máy dùng để test restore:** (không phải máy Production)

**Thời gian thực hiện:**
- Bắt đầu restore: __:__
- Database ONLINE lúc: __:__
- **Tổng thời gian restore:** _____ phút (mục tiêu RTO: ≤ 8 giờ = 480 phút)

**Kiểm chứng dữ liệu:**
- [ ] Database restore thành công, không lỗi
- [ ] Số dòng các bảng chính khớp với kỳ vọng (ghi rõ bảng đã kiểm tra)
- [ ] Đăng nhập thử ứng dụng vào database vừa restore thành công
- [ ] Dữ liệu mẫu kiểm tra đúng (ghi rõ đã xem bản ghi nào)

**Vấn đề phát sinh (nếu có):**


**Kết luận:** ☐ Đạt &nbsp;&nbsp; ☐ Không đạt (ghi rõ lý do và kế hoạch khắc phục)

---