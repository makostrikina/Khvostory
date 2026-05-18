from django.contrib import admin
from .models import Client, Doctor, Pet, Service, Appointment, ProvidedService, Receipt

admin.site.register(Client)
admin.site.register(Doctor)
admin.site.register(Pet)
admin.site.register(Service)
admin.site.register(Appointment)
admin.site.register(ProvidedService)
admin.site.register(Receipt)