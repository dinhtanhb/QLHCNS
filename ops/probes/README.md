# Review probes

Thư mục này chứa các script chẩn đoán thủ công dùng khi review. Đây không phải
là test hồi quy và không được dùng thay cho `ops/run_tests.py`.

Các probe phải dùng cấu hình test, dữ liệu giả và không được ghi vào cơ sở dữ
liệu nghiệp vụ. Nếu một finding cần được bảo vệ lâu dài, hãy chuyển nó thành
Django test có fixture cô lập trong phân hệ tương ứng.
