from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import JobPost, JobApplication
from .serializers import JobPostSerializer, JobApplicationSerializer
from rest_framework import generics

class JobPostCreateView(generics.CreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticated]


class JobApplicationCreateView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['job'] = JobPost.objects.get(id=self.kwargs['job_id'])
        return context
