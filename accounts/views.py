from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from .decorators import owner_required
from .models import CustomUser, AuditLog
from django.db import transaction
from invoices.models import BusinessProfile
from django.views.decorators.http import require_POST
from .utils import get_active_business
from django.contrib.auth.models import Group
from accounts.utils import  log_activity, get_active_business, get_client_ip
from django.contrib.auth.decorators import login_required, permission_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserUpdateForm, UserCreateForm, UserEditForm,  UserPermissionsForm

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_update.html', {'form': form})

@login_required
@owner_required
def user_list(request):
    active_business_id = request.session.get('active_business_id')
    if not active_business_id:
        return redirect("invoices:business_list")
    users = CustomUser.objects.filter(business_id=active_business_id).order_by('username')
    context = {"users": users,}
    return render(request, 'accounts/user_list.html', context)

@login_required
@owner_required
def user_create(request):
    active_business = get_active_business(request)
    if not active_business:
        return redirect('invoices:business_select')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    
                    user.business = active_business
                    raw_password = form.cleaned_data['password']
                    user.set_password(raw_password)
                    user.save()
                    selected_role = form.cleaned_data.get('role')
                    if selected_role:
                        group = Group.objects.get(name=selected_role)
                        user.groups.add(group)

                messages.success(request, f"User {user.username} has been created successfully.")
                return redirect('accounts:user_list')
            except Group.DoesNotExist:
                messages.error(request, "The selected role group does not exist. Please contact the administrator.")
            except Exception as e:
                logger.exception(e)
                messages.error(request, "An unexpected error occurred while creating the user.")
    else:
        form = UserCreateForm()
    context = {
        'form': form,
        'active_business': active_business,
    }
    return render(request, 'accounts/user_create.html', context)

@login_required
@owner_required
def user_edit(request, pk):
    active_business = get_active_business(request)
    if not active_business:
        return redirect('invoices:business_select')

    user_to_edit = get_object_or_404(CustomUser, pk=pk, business=active_business)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            selected_role_name = form.cleaned_data.get('role')
    
            if request.user == user_to_edit and selected_role_name != "Owner":
                messages.error(request, "You cannot remove your own Owner role.")
                return render(request, 'accounts/user_edit.html', {'form': form, 'active_business': active_business, 'user_to_edit': user_to_edit})
            owner_group = Group.objects.filter(name="Owner").first()
            if owner_group and user_to_edit.groups.filter(name="Owner").exists() and selected_role_name != "Owner":
                owner_count = CustomUser.objects.filter(business=active_business, groups=owner_group).count()
                if owner_count <= 1:
                    messages.error(request, "Cannot change role. The business must have at least one Owner.")
                    return render(request, 'accounts/user_edit.html', {'form': form, 'active_business': active_business, 'user_to_edit': user_to_edit})

            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    
                    raw_password = form.cleaned_data.get('password')
                    if raw_password:
                        user.set_password(raw_password)
                    
                    user.save()

                    if selected_role_name:
                        group = Group.objects.get(name=selected_role_name)
                        user.groups.clear()
                        user.groups.add(group)

                messages.success(request, f"User {user.username} has been updated successfully.")
                return redirect('accounts:user_list')
                
            except Group.DoesNotExist:
                messages.error(request, "The selected role group does not exist. Please contact the administrator.")
            except Exception as e:
                logger.error(f"Unexpected error occurred while editing user {pk}: {e}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again later.")
    else:
        form = UserEditForm(instance=user_to_edit)

    context = {
        'form': form,
        'active_business': active_business,
        'user_to_edit': user_to_edit,
    }
    return render(request, 'accounts/user_edit.html', context)

@login_required
@owner_required
@require_POST
def user_toggle_status(request, pk):
    active_business = get_active_business(request)
    if not active_business:
        return redirect('invoices:business_select')

    user_to_toggle = get_object_or_404(CustomUser, pk=pk, business=active_business)

    if request.user == user_to_toggle and user_to_toggle.is_active:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('accounts:user_list')

    owner_group = Group.objects.filter(name="Owner").first()
    is_user_owner = owner_group and user_to_toggle.groups.filter(name="Owner").exists()

    if is_user_owner and user_to_toggle.is_active and owner_group:
        active_owners_count = CustomUser.objects.filter(
            business=active_business, 
            groups=owner_group, 
            is_active=True
        ).count()
        
        if active_owners_count <= 1:
            messages.error(request, "Cannot deactivate this user. The business must have at least one active Owner.")
            return redirect('accounts:user_list')

    try:
        with transaction.atomic():
            user_to_toggle.is_active = not user_to_toggle.is_active
            user_to_toggle.save(update_fields=['is_active'])

        status_text = "activated" if user_to_toggle.is_active else "deactivated"
        messages.success(request, f"User {user_to_toggle.username} has been {status_text} successfully.")

    except Exception as e:
        logger.error(f"Unexpected error occurred while toggling status for user {pk}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please try again later.")

    return redirect('accounts:user_list')

@login_required
@owner_required
def manage_permissions(request, pk):
    active_business = get_active_business(request)
    if not active_business:
        return redirect('invoices:business_select')

    user_to_edit = get_object_or_404(CustomUser, pk=pk, business=active_business)

    if user_to_edit.is_owner:
        messages.error(request, "Owner permissions are managed automatically through the Owner role.")
        return redirect('accounts:user_list')

    if request.method == 'POST':
        form = UserPermissionsForm(request.POST, user=user_to_edit)
        if form.is_valid():
            try:
                with transaction.atomic():
                    selected_permissions = form.cleaned_data.get('permissions')
                    user_to_edit.user_permissions.set(selected_permissions)

                messages.success(request, f"Permissions for {user_to_edit.username} updated successfully.")
                return redirect('accounts:user_list')

            except Exception as e:
                logger.error(f"Error updating permissions for user {pk}: {e}", exc_info=True)
                messages.error(request, "An unexpected error occurred. Please try again later.")
    else:
        form = UserPermissionsForm(user=user_to_edit)

    context = {
        'form': form,
        'user_to_edit': user_to_edit,
        'active_business': active_business,
    }
    return render(request, 'accounts/manage_permissions.html', context)

@login_required
@owner_required
def manage_permissions(request, pk):
    active_business = get_active_business(request)

    if not active_business:
        return redirect("invoices:business_select")

    user = get_object_or_404(CustomUser, pk=pk, business=active_business,)
    if user.is_owner:
        messages.warning(request, "Owner permissions are managed through the Owner group.")
        return redirect("accounts:user_list")
    if request.method == "POST":
        form = UserPermissionsForm(request.POST, user=user)
        if form.is_valid():
            user.user_permissions.set(form.cleaned_data["permissions"])
            messages.success(request, "Permissions updated successfully.")
            return redirect("accounts:user_list")
    else:
        form = UserPermissionsForm(user=user)

    return render(
        request,
        "accounts/manage_permissions.html",
        {
            "form": form,
            "user_to_edit": user,
        },
    )

@login_required
@permission_required("accounts.view_auditlog", raise_exception=True)
def audit_log_list(request):
    logs = AuditLog.objects.all()[:100] 
    context = {'logs': logs}
    return render(request, 'accounts/audit_log_list.html', context)