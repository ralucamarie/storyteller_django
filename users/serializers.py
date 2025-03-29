from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "surname", "email", "author_name")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password", "author_name"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_author_name(self, value):
        """Ensure author_name is unique."""
        if User.objects.filter(author_name=value).exists():
            raise serializers.ValidationError("This author_name is already taken.")
        return value

    def create(self, validated_data):
        """Create user with hashed password."""
        return User.objects.create_user(**validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["author_name"] = user.author_name
        return token
