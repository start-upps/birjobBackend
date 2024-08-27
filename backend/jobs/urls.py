from django.urls import path
from .views import JobPostCreateView, JobApplicationCreateView

urlpatterns = [
    path('', JobPostCreateView.as_view(), name='job-create'),
    path('<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
]
