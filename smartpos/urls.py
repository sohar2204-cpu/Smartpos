from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Make sure 'pos' matches your actual app folder name
from pos.admin import admin_site 

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('pos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)