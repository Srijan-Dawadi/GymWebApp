from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('accounts.dashboard_urls')),
    path('members/', include('members.urls')),
    path('billing/', include('billing.urls')),
    path('attendance/', include('attendance.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'gymapp.views.error_403'
handler404 = 'gymapp.views.error_404'
handler500 = 'gymapp.views.error_500'
