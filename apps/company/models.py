from django.db import models
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

    def __str__(self):
        return self.name