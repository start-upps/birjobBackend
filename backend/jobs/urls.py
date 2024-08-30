from django.urls import path
from .views import JobListView, JobPostCreateView, JobApplicationCreateView, welcome

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),  # Maps to /api/jobs/
    path('create/', JobPostCreateView.as_view(), name='job-create'),
    path('<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
]