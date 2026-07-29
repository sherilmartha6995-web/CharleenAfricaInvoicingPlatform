from django.contrib.auth.decorators import user_passes_test

def owner_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.groups.filter(name='Owner').exists(),
        login_url='accounts:login' 
    )(view_func)