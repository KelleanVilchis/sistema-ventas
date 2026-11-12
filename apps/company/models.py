from django.db import models, transaction
from django.db.models import Q, UniqueConstraint

from apps.accounts.models import AppUser


class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    selected = models.BooleanField(default=False)
    owner = models.ForeignKey(AppUser, on_delete=models.PROTECT, related_name='owned_companies')
    created_by = models.ForeignKey(AppUser, on_delete=models.PROTECT, null=True, related_name='created_companies')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["owner"],
                condition=Q(selected=True),
                name="unique_selected_company_per_owner",
            ),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.selected and self.owner_id:
                Company.objects.filter(
                    owner_id=self.owner_id, selected=True
                ).exclude(pk=self.pk).update(selected=False)
            super().save(*args, **kwargs)