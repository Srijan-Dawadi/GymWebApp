from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .mixins import AdminRequiredMixin


class UserListView(AdminRequiredMixin, View):
    def get(self, request):
        users = User.objects.select_related('profile').order_by('username')
        return render(request, 'accounts/users.html', {'users': users})


class UserCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/user_form.html', {'action': 'Create'})

    def post(self, request):
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'staff')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/user_form.html', {'action': 'Create'})

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return render(request, 'accounts/user_form.html', {'action': 'Create'})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.profile.role = role
        user.profile.save()
        messages.success(request, f'User "{username}" created as {role}.')
        return redirect('user_list')


class UserEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        u = get_object_or_404(User, pk=pk)
        return render(request, 'accounts/user_form.html', {'action': 'Edit', 'u': u})

    def post(self, request, pk):
        u = get_object_or_404(User, pk=pk)
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'staff')
        password = request.POST.get('password', '').strip()

        u.email = email
        if password:
            u.set_password(password)
        u.save()
        u.profile.role = role
        u.profile.save()
        messages.success(request, f'User "{u.username}" updated.')
        return redirect('user_list')


class UserDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        u = get_object_or_404(User, pk=pk)
        if u == request.user:
            messages.error(request, "You can't delete your own account.")
            return redirect('user_list')
        username = u.username
        u.delete()
        messages.success(request, f'User "{username}" deleted.')
        return redirect('user_list')
