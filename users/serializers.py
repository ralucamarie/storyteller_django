from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from utils.images import build_image_filename, process_avatar
from utils.media_urls import build_media_url

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "surname",
            "email",
            "author_name",
            "avatar_url",
            "avatar_updated",
        )
        read_only_fields = (
            "id",
            "name",
            "surname",
            "email",
            "author_name",
            "avatar_url",
            "avatar_updated",
        )

    def get_avatar_url(self, obj):
        return build_media_url(obj.avatar, self.context.get("request"))


class ProfileAvatarSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def update(self, instance, validated_data):
        uploaded = validated_data["image"]
        buffer = process_avatar(uploaded)
        filename = build_image_filename("avatar")

        if instance.avatar:
            instance.avatar.delete(save=False)

        instance.avatar.save(filename, ContentFile(buffer.read()), save=False)
        instance.avatar_updated = timezone.now()
        instance.save(update_fields=["avatar", "avatar_updated"])
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password", "author_name"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_author_name(self, value):
        if User.objects.filter(author_name=value).exists():
            raise serializers.ValidationError("This author_name is already taken.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["author_name"] = user.author_name
        token["email"] = user.email
        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired reset link."})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        return user
