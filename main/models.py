from django.db import models
from django.contrib.auth.models import User
from datetime import time

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.full_name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    available_for_online_booking = models.BooleanField(default=True, verbose_name='Доступен для онлайн-записи')

    work_start = models.TimeField(default=time(9, 0))
    work_end = models.TimeField(default=time(18, 0))

    def __str__(self):
        return self.full_name

class Pet(models.Model):
    owner = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    species = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    age = models.IntegerField()
    image = models.ImageField(upload_to='pets/', blank=True, null=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.title

STATUS_CHOICES = [
    ('scheduled', 'Запланирован'),
    ('completed', 'Завершён'),
    ('cancelled', 'Отменён'),
]

class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    diagnosis = models.TextField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class ProvidedService(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total = 0
        services = ProvidedService.objects.filter(appointment=self.appointment)

        for service in services:
            total += self.service.price

        self.appointment.total_price = total
        self.appointment.save()

    def __str__(self):
        return f"{self.service.title} ({self.appointment})"

class Receipt(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Receipt #{self.id}"