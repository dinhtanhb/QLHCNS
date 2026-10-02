"""Allowlisted, authorized download of local or SharePoint attachments."""
from pathlib import PurePosixPath
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe
from .data_access import can_read_file
from .models import SecurityEvent


FILE_FIELDS = {
    'document.Document': ('uploaded_file',),
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
    try:
        opened = stored_file.open('rb')
    except FileNotFoundError:
        raise Http404
    response = FileResponse(opened, as_attachment=True, filename=path.name, content_type='application/octet-stream')
    response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    response['X-Content-Type-Options'] = 'nosniff'
    SecurityEvent.objects.create(user=request.user, action='file_download', resource=obj._meta.label_lower, record_id=str(obj.pk))
    return response
