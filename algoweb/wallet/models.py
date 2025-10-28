from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    adress = models.CharField(max_length=58)
    private_key = models.TextField()

    def __str__(self):
        return f"Wallet de {self.user.username}"

class Contacto(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contactos')
    nombre = models.CharField(max_length=100)
    email = models.EmailField("email")
    direccion = models.CharField(max_length=58)

    def __str__(self):
        return f"{self.nombre} - {self.email} - {self.direccion}"