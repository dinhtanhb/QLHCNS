"""Allowlisted, authorized download of local or SharePoint attachments."""
from pathlib import PurePosixPath
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from apps.m365.graph_client import GraphAPIError
from django.views.decorators.http import require_safe
from .data_access import can_read_file
from .models import SecurityEvent


FILE_FIELDS = {
    'document.Document': ('uploaded_file',),
    'document.PersonnelDecision': ('issued_file',),
    'document.OfficialDispatch': ('attachment',),
    'office.IncomingDocument': ('attachment',),
    'office.OutgoingDocument': ('attachment',),
    'leave.LeaveRequest': ('attachment',),
    'recruitment.Candidate': ('cv_file',),
    'm365.CompanyMedia': ('file',),
    'task.Task': ('report_file',),
    'activity.ActivityProposal': ('proposal_excel', 'proposal_pdf', 'budget_excel', 'budget_pdf'),
    'hrm.EmployeeProfileChangeRequest': ('attachment',),
}


def protected_file_response(request, stored_file, *, obj, as_attachment=True, content_type="application/octet-stream"):
    if not stored_file or not can_read_file(request.user, obj):
        raise Http404
    try:
        opened = stored_file.open("rb")
    except FileNotFoundError:
        raise Http404
    except GraphAPIError as error:
        if error.status_code == 404:
            raise Http404
        response = HttpResponse("Dịch vụ tệp tạm thời không khả dụng. Vui lòng thử lại sau.", status=503)
        try:
            retry = min(max(int(error.retry_after or 30), 1), 3600)
        except (ValueError, TypeError):
            retry = 30
        response["Retry-After"] = str(retry)
        response["Cache-Control"] = "private, no-store"
        return response
    response = FileResponse(opened, as_attachment=as_attachment,
        filename=PurePosixPath(stored_file.name).name, content_type=content_type)
    response["Content-Security-Policy"] = "sandbox; default-src 'none'"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    SecurityEvent.objects.create(user=request.user, action="file_download", resource=obj._meta.label_lower, record_id=str(obj.pk))
    return response


@login_required
@require_safe
def private_file(request, name):
    path = PurePosixPath(name)
    if not name or len(name) > 1024 or path.is_absolute() or '\\' in name or '\x00' in name or '..' in path.parts or '.' in name.split('/'):
        raise Http404
    matches = []
    for label, fields in FILE_FIELDS.items():
        model = apps.get_model(label)
        for field in fields:
            matches.extend((obj, field) for obj in model.objects.filter(**{field: name}))
    # Ambiguous references must not widen access to an attachment.
    if not matches or any(not can_read_file(request.user, obj) for obj, _ in matches):
        raise Http404
    kinds = {getattr(getattr(obj, field).storage, 'kind', 'local') for obj, field in matches}
    if len(kinds) != 1:
        raise Http404
    obj, field = matches[0]
    stored_file = getattr(obj, field)
    return protected_file_response(request, stored_file, obj=obj)
