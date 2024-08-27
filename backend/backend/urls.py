from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from jobs.views import welcome

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('', welcome, name='welcome'),
]
