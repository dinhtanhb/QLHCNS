"""
Django settings for config project.

Original project scaffold generated with Django 5.0.14; current version is pinned in requirements.txt.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

from config.env import env_flag

# BASE_DIR là thư mục 'src'
BASE_DIR = Path(__file__).resolve().parent.parent

# ROOT_DIR là thư mục gốc 'QLHCNS' chứa tệp .env
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# Secret Key & Debug
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Thiếu biến môi trường SECRET_KEY. Khai báo SECRET_KEY trong file .env (xem "
        "ROOT_DIR/.env) trước khi chạy ứng dụng — không được dùng key mặc định/công khai."
    )
DEBUG = env_flag("DEBUG")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# ==========================================
# BẢO MẬT HTTPS / COOKIE
# Theo docs/08_Deployment_Standards.md mục 32: SSL là bắt buộc trên môi
# trường Production. Máy dev cục bộ (chạy `manage.py runserver` không có
# HTTPS) sẽ KHÔNG bật các cờ này để không bị lỗi redirect vòng lặp / không
# đăng nhập được. Chỉ bật khi ENABLE_HTTPS_ENFORCEMENT=True trong .env
# (đặt True khi deploy thật, sau IIS/reverse proxy đã có chứng chỉ SSL).
# ==========================================
ENABLE_HTTPS_ENFORCEMENT = env_flag("ENABLE_HTTPS_ENFORCEMENT")

if ENABLE_HTTPS_ENFORCEMENT:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # IIS/reverse proxy chuyển tiếp thông tin HTTPS qua header này — nếu
    # không khai báo, Django sẽ không biết request gốc là HTTPS và redirect
    # lặp vô hạn.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Optional HSTS settings are environment-specific; default duration is zero for SIT.
    # Enable HSTS only after IT confirms every relevant host/subdomain uses HTTPS.
    # Keep it off by default in SIT to avoid persisting browser HTTPS policy.
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = (
        env_flag("SECURE_HSTS_INCLUDE_SUBDOMAINS")
    )
    SECURE_HSTS_PRELOAD = env_flag("SECURE_HSTS_PRELOAD")

# Production must be explicitly configured; development remains HTTP-compatible.
APP_ENV = os.getenv("APP_ENV", "development").lower()
if APP_ENV == "production":
    if DEBUG or not ENABLE_HTTPS_ENFORCEMENT:
        raise ImproperlyConfigured("Production yêu cầu DEBUG=False và ENABLE_HTTPS_ENFORCEMENT=True.")
    if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
        raise ImproperlyConfigured("Production yêu cầu SECRET_KEY ngẫu nhiên, riêng và dài ít nhất 50 ký tự.")
    if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Production yêu cầu ALLOWED_HOSTS cụ thể.")

# Các cờ này an toàn để bật ở MỌI môi trường (không phụ thuộc HTTPS):
SECURE_CONTENT_TYPE_NOSNIFF = True  # chặn trình duyệt tự đoán sai loại tệp, giảm rủi ro XSS qua upload
X_FRAME_OPTIONS = "DENY"  # chặn nhúng trang vào iframe từ site khác (chống clickjacking)

# Giới hạn phiên 8 giờ; middleware đăng xuất sau SESSION_IDLE_TIMEOUT không thao tác.
# Đóng trình duyệt kết thúc phiên nếu
# SESSION_EXPIRE_AT_BROWSER_CLOSE=True — hợp lý cho hệ thống HR có dữ liệu
# lương/CCCD nhạy cảm.
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_IDLE_TIMEOUT = int(os.getenv('SESSION_IDLE_TIMEOUT', '1800'))
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'


# Application definition

try:
    import jazzmin
    HAS_JAZZMIN = True
except ImportError:
    HAS_JAZZMIN = False

INSTALLED_APPS = (['jazzmin'] if HAS_JAZZMIN else []) + [
    'axes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'apps.common',
    'django.contrib.staticfiles',
    'apps.security',
    'apps.organization',
    'apps.hrm',
    'apps.attendance',
    'apps.leave',
    'apps.contract',
    'apps.payroll',
    'apps.portal',
    'apps.task',
    'apps.kpi',
    'apps.document',
    'apps.asset',
    'apps.recruitment',
    'apps.procurement',
    'apps.notification',
    'apps.project',
    'apps.reporting',
    'apps.office',
    'apps.planning',
    'apps.m365',
    'apps.activity',
    'apps.lifecycle',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.security.middleware.SensitiveResponseMiddleware',
    'apps.common.middleware.ApplyDueEmployeeChangesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

# Persistent database handler protects both portal and Django admin logins.
AUTHENTICATION_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']
AXES_FAILURE_LIMIT = 5
AXES_IP_FAILURE_LIMIT = max(AXES_FAILURE_LIMIT, int(os.getenv("AXES_IP_FAILURE_LIMIT", "50")))
AXES_HANDLER = "apps.security.login_handler.SharedIPAxesHandler"
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
AXES_SENSITIVE_PARAMETERS = ['username', 'ip_address', 'password', 'csrfmiddlewaretoken']
AXES_VERBOSE = False

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.portal.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Cấu hình Database
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
        }
    }
else:
    DB_TRUSTED_CONNECTION = os.getenv("DB_TRUSTED_CONNECTION", "no")
    DB_EXTRA_PARAMS = os.getenv("DB_EXTRA_PARAMS", "").strip()
    if not DB_EXTRA_PARAMS and APP_ENV == "production":
        DB_EXTRA_PARAMS = "Encrypt=yes;TrustServerCertificate=no"
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "1433"),
            "OPTIONS": {
                "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
                "trusted_connection": DB_TRUSTED_CONNECTION,
                **({"extra_params": DB_EXTRA_PARAMS} if DB_EXTRA_PARAMS else {}),
            },
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'vi'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "security.User"

LOGIN_URL = "portal:login"
LOGIN_REDIRECT_URL = "portal:dashboard"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    'default': {'BACKEND': 'apps.security.storage.PrivateFileStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# ==========================================
# TÍCH HỢP MICROSOFT 365 (SharePoint / OneDrive)
# Xem docs/16_M365_Integration_Setup.md để lấy các giá trị bên dưới.
# ==========================================
M365_TENANT_ID = os.getenv("M365_TENANT_ID", "")
M365_CLIENT_ID = os.getenv("M365_CLIENT_ID", "")
M365_CLIENT_SECRET = os.getenv("M365_CLIENT_SECRET", "")

# Site SharePoint sẽ dùng làm nơi lưu tài liệu, ví dụ:
#   URL đầy đủ: https://congty.sharepoint.com/sites/IHRMS
#   -> M365_SHAREPOINT_HOSTNAME=congty.sharepoint.com
#   -> M365_SHAREPOINT_SITE_PATH=/sites/IHRMS
M365_SHAREPOINT_HOSTNAME = os.getenv("M365_SHAREPOINT_HOSTNAME", "")
M365_SHAREPOINT_SITE_PATH = os.getenv("M365_SHAREPOINT_SITE_PATH", "")

# Bật lưu trữ qua SharePoint/OneDrive thay vì đĩa cục bộ. Mặc định TẮT để hệ
# thống vẫn chạy bình thường (lưu vào MEDIA_ROOT) trong lúc chờ IT cấp đủ
# Tenant ID / Client ID / Client Secret / site SharePoint ở trên.
M365_STORAGE_ENABLED = env_flag("M365_STORAGE_ENABLED")

# One SharePoint document library (a Graph drive) contains per-feature folders.
# Legacy M365_LIBRARY_DOCUMENTS remains a fallback for the former library setting.
M365_SHAREPOINT_LIBRARY = os.getenv(
    "M365_SHAREPOINT_LIBRARY", os.getenv("M365_LIBRARY_DOCUMENTS", "Documents")
)
M365_FOLDER_MAP = {
    "documents": os.getenv("M365_FOLDER_DOCUMENTS", ""),
    # CongVan is retained for legacy dispatch files and internal directives.
    # New incoming/outgoing attachments use their direction-specific folders.
    "dispatches": os.getenv("M365_FOLDER_DISPATCHES", os.getenv("M365_LIBRARY_DISPATCHES", "CongVan")),
    "incoming_docs": os.getenv("M365_FOLDER_INCOMING", os.getenv("M365_LIBRARY_INCOMING", "CongVanDen")),
    "outgoing_docs": os.getenv("M365_FOLDER_OUTGOING", os.getenv("M365_LIBRARY_OUTGOING", "CongVanDi")),
    "leave": os.getenv("M365_FOLDER_LEAVE", os.getenv("M365_LIBRARY_LEAVE", "DonNghiPhep")),
    "recruitment_cv": os.getenv("M365_FOLDER_CV", os.getenv("M365_LIBRARY_CV", "HoSoUngVien")),
    "assets": os.getenv("M365_FOLDER_ASSETS", os.getenv("M365_LIBRARY_ASSETS", "TaiSanHinhAnh")),
    "activity_reports": os.getenv(
        "M365_FOLDER_ACTIVITY_REPORTS", os.getenv("M365_LIBRARY_ACTIVITY_REPORTS", "BaoCaoHoatDong")
    ),
    "activity_proposals": os.getenv("M365_FOLDER_ACTIVITY_PROPOSALS", "DeXuatHoatDong"),
}
M365_UPLOAD_PREFIX_MAP = {
    "documents": "documents",
    "dispatches": "dispatches",
    "incoming_docs": "incoming_docs",
    "outgoing_docs": "outgoing_docs",
    "leave": "leave-requests",
    "recruitment_cv": "candidates/cv",
    "assets": "company-media",
    "activity_reports": "activity-reports",
    "activity_proposals": "activity-proposals",
}

# ==========================================
# CẤU HÌNH GIAO DIỆN QUẢN TRỊ ADMINLTE 3 (JAZZMIN)
# ==========================================
JAZZMIN_SETTINGS = {
    "site_title": "IHRMS - Quản Trị Hệ Thống",
    "site_header": "IHRMS",
    "site_brand": "IHRMS Admin",
    "welcome_sign": "Hệ thống Quản trị Hành chính & Nhân sự (IHRMS)",
    "copyright": "IHRMS Enterprise",
    "search_model": ["hrm.Employee", "organization.Department"],
    
    # Menu ngang phía trên (Top menu)
    "topmenu_links": [
        {"name": "Về giao diện sử dụng", "url": "/portal/", "icon": "fas fa-arrow-left", "new_window": False},
        {"name": "Trung tâm Báo cáo", "url": "/reports/", "icon": "fas fa-chart-pie"},
        {"name": "Tổng quan Quản trị", "url": "admin:index", "icon": "fas fa-tachometer-alt"},
    ],

    # Làm liên kết quay về portal thành nút nổi bật, luôn dễ thấy trên navbar.
    "custom_css": "css/admin.css",

    # Menu tài khoản góc trên bên phải
    "usermenu_links": [
        {"name": "Hồ sơ cá nhân", "url": "/portal/profile/", "icon": "fas fa-id-card"},
        {"name": "Cổng thông tin", "url": "/portal/", "icon": "fas fa-home"},
        {"name": "Báo cáo thống kê", "url": "/reports/", "icon": "fas fa-chart-bar"},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["common"],

    # Thứ tự phân nhóm menu theo luồng nghiệp vụ
    "order_with_respect_to": [
        "hrm",
        "organization",
        "attendance",
        "leave",
        "contract",
        "payroll",
        "task",
        "project",
        "planning",
        "kpi",
        "document",
        "asset",
        "recruitment",
        "procurement",
        "notification",
        "reporting",
        "security",
        "auth",
    ],

    # Biểu tượng FontAwesome cho các phân hệ và bảng
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "security.User": "fas fa-user-shield",
        "security.Role": "fas fa-id-badge",
        "hrm.Employee": "fas fa-user-tie",
        "hrm.EmployeeTransfer": "fas fa-exchange-alt",
        "hrm.EmployeePromotion": "fas fa-level-up-alt",
        "hrm.EmployeeReward": "fas fa-award",
        "hrm.EmployeeDiscipline": "fas fa-exclamation-triangle",
        "organization.Organization": "fas fa-building",
        "organization.Department": "fas fa-sitemap",
        "organization.Position": "fas fa-briefcase",
        "organization.JobTitle": "fas fa-user-tag",
        "attendance.Attendance": "fas fa-calendar-check",
        "attendance.WorkShift": "fas fa-clock",
        "attendance.Holiday": "fas fa-calendar-day",
        "attendance.WorkingCalendar": "fas fa-calendar",
        "attendance.TimesheetEntry": "fas fa-user-clock",
        "attendance.MonthlyAttendanceSummary": "fas fa-calculator",
        "attendance.ProjectTimeAllocation": "fas fa-chart-pie",
        "project.Project": "fas fa-project-diagram",
        "planning.HeadcountPlan": "fas fa-users-cog",
        "planning.AdminBudgetPlan": "fas fa-coins",
        "planning.WeeklySchedule": "fas fa-calendar-week",
        "leave.LeaveRequest": "fas fa-plane-departure",
        "leave.LeaveType": "fas fa-umbrella-beach",
        "leave.LeaveBalance": "fas fa-wallet",
        "leave.LeaveApproval": "fas fa-check-circle",
        "contract.Contract": "fas fa-file-signature",
        "contract.ContractType": "fas fa-file-contract",
        "contract.ContractAppendix": "fas fa-paperclip",
        "payroll.Payroll": "fas fa-money-bill-wave",
        "payroll.PayrollPeriod": "fas fa-calendar-alt",
        "task.Task": "fas fa-tasks",
        "kpi.KPI": "fas fa-chart-line",
        "document.Document": "fas fa-file-alt",
        "document.DocumentCategory": "fas fa-folder",
        "document.DocumentApproval": "fas fa-stamp",
        "document.DispatchBook": "fas fa-book",
        "document.OfficialDispatch": "fas fa-mail-bulk",
        "document.DispatchTracking": "fas fa-route",
        "asset.Asset": "fas fa-laptop",
        "recruitment.RecruitmentRequest": "fas fa-user-plus",
        "procurement.ProcurementRequest": "fas fa-shopping-cart",
        "notification.Notification": "fas fa-bell",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "changeform_format": "horizontal_tabs",
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-primary navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==========================================
# LOGGING
# Theo docs/08_Deployment_Standards.md mục 27: log level Info/Warning/Error/
# Critical, ghi vào thư mục /Logs. Tự xoay vòng file (5MB/file, giữ 30 file
# gần nhất ~ tương đương chuẩn giữ log 30 ngày ở mục 19).
# ==========================================
LOG_DIR = ROOT_DIR / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"safe_exception": {"()": "apps.security.logging.SafeExceptionFilter"}},
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["safe_exception"],
            "formatter": "verbose",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filters": ["safe_exception"],
            "filename": LOG_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 30,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filters": ["safe_exception"],
            "filename": LOG_DIR / "error.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 30,
            "formatter": "verbose",
            "level": "ERROR",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "app_file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            # Namespace chung cho log nghiệp vụ tự viết trong code, dùng:
            #   import logging; logger = logging.getLogger(__name__)
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
