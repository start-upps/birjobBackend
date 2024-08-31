from rest_framework import viewsets, permissions, generics
from .models import JobPost, JobApplication
from .serializers import JobPostSerializer, JobApplicationSerializer
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework import status

# Welcome view for the platform
def welcome(request):
    return HttpResponse("Welcome to the Job Platform!")

# Custom permission class to allow only the owner of the job to edit or delete it
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the job post
        return obj.posted_by == request.user

# ViewSet for handling Job Posts with full CRUD functionality
class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
 
# View for applying to a job
class JobApplicationCreateView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can apply to jobs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['job'] = JobPost.objects.get(id=self.kwargs['job_id'])
        return context
