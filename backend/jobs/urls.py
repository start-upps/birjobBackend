# from django.urls import path
# from .views import JobListView, JobPostCreateView, JobApplicationCreateView, welcome

# urlpatterns = [
#     path('', welcome, name='welcome'),
#     path('jobs/', JobListView.as_view(), name='job-list'),
#     path('jobs/create/', JobPostCreateView.as_view(), name='job-create'),
#     path('jobs/<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),
# ]


from django.urls import path
from .views import JobListView, JobPostCreateView, JobApplicationCreateView, welcome

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),  # Maps to /api/jobs/
    path('create/', JobPostCreateView.as_view(), name='job-create'),  # Maps to /api/jobs/create/
    path('<int:job_id>/apply/', JobApplicationCreateView.as_view(), name='job-apply'),  # Maps to /api/jobs/<job_id>/apply/
]
