from django.urls import path, include
from .views import JobListView, JobPostViewSet, JobApplicationCreateView, JobDetailView, JobApplicationsListView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'jobs', JobPostViewSet)

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),  # Maps to /api/jobs/
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),  # Maps to /api/jobs/<job_id>/
    path('<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
    path('<int:job_id>/applicants/', JobApplicationsListView.as_view(), name='job-applicants'),  # View applicants
    path('', include(router.urls)),  # Include the router URLs for the JobPostViewSet
]
