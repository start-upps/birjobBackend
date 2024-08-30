from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import JobPost, JobApplication
from .serializers import JobPostSerializer, JobApplicationSerializer
from django.http import HttpResponse

def welcome(request):
    return HttpResponse("Welcome to the Job Platform!")

class JobPostCreateView(generics.ListCreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post']

# View for applying to a job
class JobApplicationCreateView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can apply to jobs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['job'] = JobPost.objects.get(id=self.kwargs['job_id'])
        return context

# View for listing jobs (accessible to everyone)
class JobListView(generics.ListAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [AllowAny]  # Non-authenticated users can view jobs
