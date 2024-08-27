from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import JobPost, JobApplication
from .serializers import JobPostSerializer, JobApplicationSerializer
from rest_framework import generics
from django.http import HttpResponse

def welcome(request):
    return HttpResponse("Welcome to the Job Platform!")

class JobPostCreateView(generics.ListCreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

class JobApplicationCreateView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['job'] = JobPost.objects.get(id=self.kwargs['job_id'])
        return context

class JobListView(generics.ListAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [AllowAny]  # Allow non-authenticated users to view jobs

