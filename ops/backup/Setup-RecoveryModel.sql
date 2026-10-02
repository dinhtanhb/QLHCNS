-- ============================================================
-- Setup-RecoveryModel.sql
-- Chạy 1 LẦN DUY NHẤT trước khi bắt đầu dùng backup transaction log.
--
-- Vì sao cần: mặc định SQL Server Express thường tạo database mới ở chế độ
-- "Simple recovery" — ở chế độ này KHÔNG backup transaction log được (log
-- tự xoá sau mỗi checkpoint). Muốn backup log mỗi giờ theo đúng chuẩn trong
-- docs/08_Deployment_Standards.md mục 18, database phải ở "Full recovery".
--
-- Cách chạy: mở SSMS (Windows Authentication) -> New Query -> dán nội dung
-- này -> Execute (F5).
-- ============================================================

-- Rà đúng tên database và đường dẫn trước khi chạy; không dùng cho database khác.
USE master;
GO

ALTER DATABASE qlhcns SET RECOVERY FULL;
GO

-- Sau khi đổi sang FULL, chuỗi log backup chỉ thật sự bắt đầu sau lần FULL
-- BACKUP đầu tiên. Chạy full backup ngay 1 lần thủ công tại đây để "mở
-- chuỗi", trước khi lên lịch tự động qua Task Scheduler:
BACKUP DATABASE qlhcns
TO DISK = 'D:\QLHCNS\Backups\Daily\qlhcns_full_init.bak'
WITH INIT, NO_COMPRESSION, CHECKSUM, STATS = 10;
RESTORE VERIFYONLY FROM DISK = N'D:\QLHCNS\Backups\Daily\qlhcns_full_init.bak' WITH CHECKSUM;
GO

-- Kiểm tra lại: cột recovery_model_desc phải hiện 'FULL'
SELECT name, recovery_model_desc FROM sys.databases WHERE name = 'qlhcns';
GO
