from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobPostViewSet, JobApplicationCreateView, welcome

router = DefaultRouter()
router.register(r'jobs', JobPostViewSet)

urlpatterns = [
    path('welcome/', welcome, name='welcome'),
    path('jobs/<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
    path('', include(router.urls)),
]
