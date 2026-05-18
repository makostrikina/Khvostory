from .views import is_admin

def admin_status(request):

    return {

        'is_admin': is_admin(request.user)

    }