
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('VICE_PRINCIPAL', 'Vice Principal'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='VICE_PRINCIPAL'
    )

    def __str__(self):
        return f"{self.username} - {self.role}"
class Teacher(models.Model):
    teacher_id = models.CharField(
    max_length=20,
    unique=True,
    blank=True,
    null=True
)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)

    def __str__(self):
        return self.full_name