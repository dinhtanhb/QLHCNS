"""Render a static developer kitchen sink. No production URL or database is used."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from django.conf import settings
settings.configure(LANGUAGE_CODE="vi", NUMBER_GROUPING=3,
                   TIME_ZONE="Asia/Ho_Chi_Minh", USE_I18N=True, USE_TZ=True, INSTALLED_APPS=[])
import django
django.setup()
from django import forms
from django.template import Context, Engine
from django.core.paginator import Paginator
from apps.common.ui_status import STATUS_BADGES

class Example(forms.Form):
    title = forms.CharField(label="Tên mẫu", help_text="Dữ liệu giả, không lưu vào hệ thống.")
    amount = forms.DecimalField(label="Số tiền", min_value=0, help_text="Đơn vị VND.")

engine = Engine(dirs=[str(ROOT / "src/templates"), str(ROOT / "src/apps/portal/templates")],
                libraries={"ui_components": "apps.common.templatetags.ui_components"},
                builtins=["apps.common.templatetags.ui_numbers"])
errors = Example({"title": "", "amount": "không phải số"}, prefix="error")
errors.is_valid()
context = Context({"example": Example(prefix="sample"), "error_form": errors,
                   "families": STATUS_BADGES, "page_obj": Paginator(list(range(45)), 20).get_page(2),
                   "pagination_query": "q=du-lieu-gia"})
source = (ROOT / "docs/ui_components_source.html").read_text(encoding="utf-8")
output = engine.from_string(source).render(context)
(ROOT / "docs/ui_components.html").write_text(output, encoding="utf-8")
print("Rendered docs/ui_components.html without database access.")
