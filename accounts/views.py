import json
import time
from collections import defaultdict

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# ── Login brute-force throttle (in-memory, single-process) ───────────────
# Waitress runs one process, so a process-local attempt log is adequate.
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECS  = 900   # 15 minutes
_LOGIN_COOLDOWN_SECS = 900

_login_attempts = defaultdict(list)  # ip -> [timestamps of failed logins]


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _login_throttled(ip):
    now = time.time()
    recent = [t for t in _login_attempts[ip] if now - t < _LOGIN_WINDOW_SECS]
    _login_attempts[ip] = recent
    return len(recent) >= _LOGIN_MAX_ATTEMPTS


@method_decorator(csrf_exempt, name='dispatch')
class HealthView(View):
    """Health check endpoint for readiness/liveness probes and pyupdater."""
    def get(self, request):
        # Quick DB connectivity check
        from django.db import connection
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        return JsonResponse({
            'status': 'healthy' if db_ok else 'degraded',
            'database': 'connected' if db_ok else 'disconnected',
            'version': '1.0.0',  # Update with your app version
        }, status=200 if db_ok else 503)


from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        ip = _client_ip(request)

        if _login_throttled(ip):
            # Block BEFORE any auth attempt — we don't want to burn a PBKDF2
            # hash (or leak anything) for a throttled request.
            from django.contrib import messages as django_messages
            django_messages.error(request, 'Too many failed attempts. Please try again in a few minutes.')
            return render(request, self.template_name, {'form': AuthenticationForm(request=request)})

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            _login_attempts[ip] = []
            user = form.get_user()
            login(request, user)
            # Newly bootstrapped users must set their own password immediately.
            profile = getattr(user, 'profile', None)
            if profile is not None and profile.must_change_password:
                return redirect('change_password')
            # Only allow in-app (relative) redirect targets to avoid open redirects.
            next_url = request.GET.get('next', '')
            if next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('dashboard')
        _login_attempts[ip].append(time.time())
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        profile = self.request.user.profile
        if profile.must_change_password:
            profile.must_change_password = False
            profile.save(update_fields=['must_change_password'])
        return super().form_valid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')
