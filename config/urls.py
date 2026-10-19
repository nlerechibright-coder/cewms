from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # 1. Redirect the root URL ("/") to the login page
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='home'),
    
    # 2. Admin panel
    path('admin/', admin.site.urls),
    
    # 3. App URLs
    path('accounts/', include('apps.accounts.urls')),
    path('complaints/', include('apps.complaints.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)