from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobPostViewSet, JobApplicationViewSet

router = DefaultRouter()
router.register(r'job-posts', JobPostViewSet)
router.register(r'job-applications', JobApplicationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
