from django.contrib import admin

from apps.lifecycle.models import (
    ChecklistTemplate, ChecklistTemplateItem, EmployeeLifecycleCase, LifecycleChecklistItem,
)


class ChecklistTemplateItemInline(admin.TabularInline):
    model = ChecklistTemplateItem
    extra = 1


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ("template_code", "template_name", "template_type", "is_active")
    list_filter = ("template_type", "is_active")
    search_fields = ("template_code", "template_name")
    inlines = (ChecklistTemplateItemInline,)


@admin.register(EmployeeLifecycleCase)
class EmployeeLifecycleCaseAdmin(admin.ModelAdmin):
    list_display = ("employee", "case_type", "effective_date", "status", "template")
    list_filter = ("case_type", "status")
    search_fields = ("employee__employee_code", "employee__full_name", "triggering_event_ref")
    readonly_fields = ("triggering_event_ref",)


@admin.register(LifecycleChecklistItem)
class LifecycleChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "case", "assigned_to_user", "due_date", "status")
    list_filter = ("status", "responsible_role_code", "requires_asset_return")
    search_fields = ("item_name", "case__employee__employee_code", "case__employee__full_name")
