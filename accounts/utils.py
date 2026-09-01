from django.shortcuts import get_object_or_404
from invoices.models import BusinessProfile
from .models import AuditLog

def get_active_business(request):
    active_business_id = request.session.get("active_business_id")

    if not active_business_id:
        return None

    return get_object_or_404(
        BusinessProfile,
        id=active_business_id,
        owner=request.user,
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_activity(request, action, model_name="", object_id="", object_repr="", description=""):
    
    user = request.user if request.user.is_authenticated else None
    business = getattr(user, "business", None) if user else None
    ip_address = get_client_ip(request)

    AuditLog.objects.create(
        user=user,
        business=business,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else "",
        object_repr=object_repr,
        description=description,
        ip_address=ip_address
    )