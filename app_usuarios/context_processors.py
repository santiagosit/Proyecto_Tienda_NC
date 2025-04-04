from .models import Profile

def add_profile_to_context(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None
        return {'profile': profile}
    return {}