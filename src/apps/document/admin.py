from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import DocumentCategory, Document, DocumentApproval, DispatchBook, OfficialDispatch, DispatchTracking

VIEW_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DIRECTOR", "DEPT_MANAGER")


class DocumentCategoryAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")


admin.site.register(DocumentCategory, DocumentCategoryAdmin)


@admin.register(Document)
class DocumentAdmin(BaseAuditAdmin):
    list_display = ("document_no", "document_name", "category", "version_no", "status")
    list_filter = ("status", "category")
    search_fields = ("document_no", "document_name")
    view_roles = VIEW_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code not in ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER"):
            from django.db.models import Q
            return qs.filter(~Q(status="Draft") | Q(created_by=request.user))
        return qs


@admin.register(DocumentApproval)
class DocumentApprovalAdmin(BaseAuditAdmin):
    list_display = ("document", "approver", "decision", "approval_date")
    view_roles = VIEW_ROLES
    edit_roles = ()  # chỉ sinh tự động qua nút Duyệt trong Portal


@admin.register(DispatchBook)
class DispatchBookAdmin(BaseAuditAdmin):
    list_display = ("book_code", "book_name", "book_type", "year", "current_number", "is_active")
    list_filter = ("book_type", "year", "is_active")
    search_fields = ("book_code", "book_name")
    view_roles = VIEW_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


class DispatchTrackingInline(admin.TabularInline):
    model = DispatchTracking
    extra = 1
    fields = ("actor", "action_type", "comment", "action_date")
    readonly_fields = ("action_date",)


@admin.register(OfficialDispatch)
class OfficialDispatchAdmin(BaseAuditAdmin):
    list_display = (
        "dispatch_no", "dispatch_type", "title", "issuing_organization",
        "received_or_sent_date", "urgency_level", "department", "assigned_to", "status"
    )
    list_filter = ("dispatch_type", "status", "urgency_level", "security_level", "dispatch_book", "department")
    search_fields = ("dispatch_no", "original_doc_no", "title", "issuing_organization")
    date_hierarchy = "received_or_sent_date"
    inlines = [DispatchTrackingInline]
    view_roles = VIEW_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")

    def scope_queryset(self, request, qs):
        from apps.security.data_access import visible_dispatches_for
        return visible_dispatches_for(request.user, qs)


@admin.register(DispatchTracking)
class DispatchTrackingAdmin(BaseAuditAdmin):
    list_display = ("dispatch", "actor", "action_type", "action_date")
    list_filter = ("action_type",)
    search_fields = ("dispatch__dispatch_no", "dispatch__title", "actor__full_name")
    view_roles = VIEW_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")

    def scope_queryset(self, request, qs):
        from apps.security.data_access import visible_dispatches_for
        return qs.filter(dispatch__in=visible_dispatches_for(request.user))
