from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import json
from friend.models import FriendList


class MyAccountManager(BaseUserManager):
 
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            raise ValueError("Users must have an username.")
        user = self.model(
            email=self.normalize_email(email),
            username = username
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


def get_profile_image_filepath(self, filename):
    return f'profile_image/{str(self.pk)}/{"profile_image.png"}'

def get_default_profile_image():
    return "default_profile_image/profile_image.png"


class Account(AbstractBaseUser):

    email = models.EmailField(verbose_name="email", max_length=100, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    date_joined = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    profile_image = models.ImageField(max_length=255, upload_to=get_profile_image_filepath, null=True, blank=True, default=get_default_profile_image)
    hide_email = models.BooleanField(default=True)

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        """
        Admin permissions
        """
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def get_profile_image_filename(self):
        """
        return the name of the uploaded file
        """
        return str(self.profile_image)[str(self.profile_image).index(f'profile_image{str(self.pk)}/'):]


@receiver(post_save, sender=Account)
def user_save(sender, instance, **kwargs):
    FriendList.objects.get_or_create(user=instance)