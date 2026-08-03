from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    """Block access to the app until a user flagged with
    must_change_password has set a new password.

    Only the password-change page, logout and login are reachable in that state.
    """

    _ALLOWED_PREFIXES = ('/accounts/password/', '/accounts/logout/', '/accounts/login/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            must_change = getattr(getattr(request.user, 'profile', None), 'must_change_password', False)
            if must_change and not request.path.startswith(self._ALLOWED_PREFIXES):
                return redirect('change_password')
        return self.get_response(request)
