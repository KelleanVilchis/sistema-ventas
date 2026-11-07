from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserType(models.TextChoices):
    ADMIN = 'ADM','Administrador'
    VENDEDOR = 'EMP','Empleado'

class AppUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, is_superuser=False, is_staff=False, is_active=True):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)        
        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.active = is_active
        user.save(using=self._db)
        return user
        
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")

        user = self.model(
            email=self.normalize_email(email)
        )
        
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)        
        user.is_superuser = True
        user.is_staff = True
        user.staff = True
        user.active = True
        user.save(using=self._db)
        return user 



class AppUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    user_type = models.CharField(choices=UserType.choices,default=UserType.VENDEDOR ,max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = AppUserManager()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'