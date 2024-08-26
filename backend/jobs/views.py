from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import JobPost, JobApplication
from .serializers import JobPostSerializer, JobApplicationSerializer

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super(JobPostViewSet, self).get_permissions()


class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save()
