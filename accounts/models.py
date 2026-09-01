from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class CustomUser(AbstractUser):
    business = models.ForeignKey("invoices.BusinessProfile", on_delete=models.CASCADE, related_name="users", null=True, blank=True,)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=14,blank=True, null=True)
    first_name = models.CharField(max_length=50,blank=True)
    last_name = models.CharField(max_length=50,blank=True)

    class Meta:
        ordering = ["username"]
    @property
    def is_owner(self):
        return self.groups.filter(name="Owner").exists()
    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username
    @property
    def role(self):
        group = self.groups.first()
        return group.name if group else "No Role"

    def __str__(self):
        return self.username

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('LOGIN', 'Logged In'),
        ('LOGOUT', 'Logged Out'),
        ("PRINT", "Printed"),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('PAYMENT', 'Payment'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,blank=True, related_name='audit_logs')
    business = models.ForeignKey('invoices.BusinessProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50,  blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['business']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        business = self.business.business_name if self.business else "No Business"
        user = self.user.username if self.user else "System"

        return (
            f"{business} | "
            f"{user} | "
            f"{self.action} {self.model_name} "
            f"({self.object_id})"
        )