from rest_framework import serializers
from .models import CustomUser, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    is_recruiter = serializers.BooleanField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password', 'is_recruiter')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        is_recruiter = validated_data.pop('is_recruiter', False)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        if is_recruiter:
            Profile.objects.create(user=user)
        return user



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims if needed
        token['email'] = user.email
        return token
