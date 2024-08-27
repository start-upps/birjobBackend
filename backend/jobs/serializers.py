from rest_framework import serializers
from .models import JobPost, JobApplication

class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = ['posted_by', 'posted_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['posted_by'] = request.user
        return super().create(validated_data)


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ['job', 'applied_at']

    def create(self, validated_data):
        validated_data['job'] = self.context['job']
        return super().create(validated_data)
