def django_auth(request):
    if request.user.is_authenticated:
        return request.user
    return None
