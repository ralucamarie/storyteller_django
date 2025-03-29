from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):

    def get_by_natural_key(self, email):
        """Allows Django to retrieve users using the email field."""
        return self.get(email=email)

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a user with an email instead of a username."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)



class User(AbstractBaseUser):
    name = models.CharField(max_length=150, blank=True, null=True)
    surname = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    author_name = models.CharField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)  # Required for Django authentication
    is_staff = models.BooleanField(default=False)  # Required for Django admin
    is_superuser = models.BooleanField(default=False)  # Needed for superuser check

    # Avoid conflicts with Django's default groups and permissions
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",  # ✅ Change related_name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",  # ✅ Change related_name
        blank=True
    )

    username = None  # Remove the default username field
    USERNAME_FIELD = "email"  # ✅ Use email for authentication
    REQUIRED_FIELDS = ["name", "surname", "author_name"]  # ✅ Mandatory fields

    objects = UserManager()

    def __str__(self):
        return self.email
