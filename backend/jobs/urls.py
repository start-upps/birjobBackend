from django.urls import path
from .views import JobListView, JobPostCreateView, JobApplicationCreateView

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),
    path('<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
    path('create/', JobPostCreateView.as_view(), name='job-create'),
]
