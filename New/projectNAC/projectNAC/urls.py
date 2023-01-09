from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.urls import path, include

from projectNAC import views as local_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', local_views.hellow_world),
    path('home', include(('fileItems.urls', 'fileItems'), namespace='fileItems')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

