from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomSetPasswordForm, CustomPasswordChangeForm

app_name = 'accounts'

urlpatterns = [
path('register/', views.register_view, name='register'),
path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
path('logout/', auth_views.LogoutView.as_view(), name='logout'),
path('profile/', views.profile_view, name='profile'),
path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html", 
        email_template_name="accounts/password_reset_email.html", 
        subject_template_name="accounts/password_reset_subject.txt",
        success_url='/accounts/password-reset/done/'
    ), name="password_reset"),
path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"
    ), name="password_reset_done"),
path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        form_class=CustomSetPasswordForm,
        success_url='/accounts/reset/done/'
    ), name="password_reset_confirm"),
path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"
    ), name="password_reset_complete"),
path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        form_class=CustomPasswordChangeForm,
        success_url='/accounts/password-change/done/'
    ), name='password_change'),
    
path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
path('profile/edit/', views.profile_update_view, name='profile_update'),
path("users/", views.user_list, name="user_list"),
path("users/add/", views.user_create, name="user_create"),
path("users/<int:pk>/edit/", views.user_update, name="user_update"),
path("users/<int:pk>/deactivate/", views.user_deactivate, name="user_deactivate"),
]