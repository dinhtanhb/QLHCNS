from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, *, user=None):
        now = timezone.now()
        values = {"is_deleted": True, "deleted_date": now, "modified_date": now}
        if user is not None:
            values["deleted_by"] = user
            values["modified_by"] = user
        count = self.filter(is_deleted=False).update(**values)
        return count, {self.model._meta.label: count}

    def hard_delete(self):
        return super().delete()

    def restore(self, *, user=None):
        now = timezone.now()
        values = {"is_deleted": False, "deleted_date": None, "deleted_by": None, "modified_date": now}
        if user is not None:
            values["modified_by"] = user
        count = self.filter(is_deleted=True).update(**values)
        return count


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    use_in_migrations = False

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseAuditModel(models.Model):
    """
    Base bắt buộc cho MỌI model nghiệp vụ.
    Theo 00_Project_Charter.md mục 12 và 03_Database_Design.md mục 3.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+", db_column="CreatedBy",
    )
    created_date = models.DateTimeField(auto_now_add=True, db_column="CreatedDate")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+", db_column="ModifiedBy",
    )
    modified_date = models.DateTimeField(auto_now=True, null=True, db_column="ModifiedDate")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+", db_column="DeletedBy",
    )
    deleted_date = models.DateTimeField(null=True, blank=True, db_column="DeletedDate")
    is_deleted = models.BooleanField(default=False, db_column="IsDeleted")

    objects = SoftDeleteManager()
    all_objects = models.Manager.from_queryset(SoftDeleteQuerySet)()

    def delete(self, using=None, keep_parents=False, *, user=None):
        return type(self).all_objects.using(using or self._state.db).filter(pk=self.pk).delete(user=user)

    def hard_delete(self, using=None, keep_parents=False):
        return type(self).all_objects.using(using or self._state.db).filter(pk=self.pk).hard_delete()

    def restore(self, *, user=None):
        return type(self).all_objects.using(self._state.db).filter(pk=self.pk).restore(user=user)

    class Meta:
        abstract = True
