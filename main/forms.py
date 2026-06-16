from django import forms
from .models import Client, Pet, Doctor, Service, Appointment, ProvidedService
from .models import *
from datetime import date
from django.contrib.auth.models import User

TIME_CHOICES = [

    ('09:00', '09:00'),
    ('09:30', '09:30'),

    ('10:00', '10:00'),
    ('10:30', '10:30'),

    ('11:00', '11:00'),
    ('11:30', '11:30'),

    ('12:00', '12:00'),
    ('12:30', '12:30'),

    ('13:00', '13:00'),
    ('13:30', '13:30'),

    ('14:00', '14:00'),
    ('14:30', '14:30'),

    ('15:00', '15:00'),
    ('15:30', '15:30'),

    ('16:00', '16:00'),
    ('16:30', '16:30'),

    ('17:00', '17:00'),
    ('17:30', '17:30'),

]

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['user', 'full_name', 'phone', 'email']
        labels = {
            'user': 'Пользователь',
            'full_name': 'ФИО',
            'phone': 'Телефон',
            'email': 'Email'
        }
    
    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(groups__name='Client')
        self.fields['user'].required = True

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['owner', 'species', 'breed', 'age',  'name', 'image']
        labels = {
            'owner': 'Владелец',
            'species': 'Вид',
            'breed': 'Порода',
            'age': 'Возраст',
            'name': 'Кличка',
            'image': 'Изображение'
        }

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['user', 'full_name', 'specialization', 'available_for_online_booking']
        labels = {
            'user': 'Пользователь',
            'full_name': 'ФИО',
            'specialization': 'Специализация'
        }
    #выбор только врачей в ячейке пользователь
    def __init__(self, *args, **kwargs):
        super(DoctorForm, self).__init__(*args, **kwargs)

        self.fields['user'].queryset = User.objects.filter(
            groups__name='Doctor'
        )

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'price']
        labels = {
            'title': 'Название',
            'price': 'Цена'
        }

class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            'client',
            'pet',
            'doctor',
            'appointment_date',
            'appointment_time',
            'diagnosis',
            'notes',
            'status'
        ]

        labels = {
            'client': 'Владелец',
            'pet': 'Питомец',
            'doctor': 'Ветеринар',
            'appointment_date': 'Дата',
            'appointment_time': 'Время',
            'diagnosis': 'Диагноз',
            'notes': 'Заметки',
            'status': 'Статус'
        }

        widgets = {

            'appointment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'min': date.today().isoformat()
                }
            ),

            'appointment_time': forms.Select(
                choices=TIME_CHOICES
            ),

        }

    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['doctor'].queryset = Doctor.objects.filter(
            available_for_online_booking=True
        )

        if user:

            #клиент
            if user.groups.filter(name='Client').exists():

                client = Client.objects.get(user=user)

                self.fields['pet'].queryset = Pet.objects.filter(
                    owner=client
                )

                # скрываем владельца
                self.fields['client'].initial = client

                self.fields['client'].widget = forms.HiddenInput()

                # клиент не должен менять статус
                self.fields['status'].widget = forms.HiddenInput()

                self.fields['status'].initial = 'scheduled'

            #админ и врач
            else:

                self.fields['pet'].queryset = Pet.objects.all()

                self.fields['client'].queryset = Client.objects.all()

    #валидация
    def clean(self):

        cleaned_data = super().clean()

        doctor = cleaned_data.get('doctor')

        appointment_time = cleaned_data.get(
            'appointment_time'
        )

        appointment_date = cleaned_data.get(
            'appointment_date'
        )

        if doctor and appointment_time and appointment_date:

            #проверка рабочего времени
            if (
                appointment_time < doctor.work_start or
                appointment_time > doctor.work_end
            ):

                raise forms.ValidationError(
                    'Врач не работает в это время'
                )

            #проверка занятости времени
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            )

            #исключаем текущий объект при редактировании
            if self.instance.pk:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise forms.ValidationError(
                    'Это время уже занято'
                )

        return cleaned_data

class ProvidedServiceForm(forms.ModelForm):
    class Meta:

        model = ProvidedService

        fields = [
            'appointment',
            'service',
            'quantity'
        ]

        labels = {
            'appointment': 'Приём',
            'service': 'Услуга',
            'quantity': 'Количество'
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        #красивый вывод приёмов
        self.fields['appointment'].label_from_instance = (
            lambda obj:
            f'{obj.id} | '
            f'{obj.pet.name} | '
            f'{obj.appointment_date} | '
            f'{obj.doctor.full_name}'
        )

        #и услуг
        self.fields['service'].label_from_instance = (
            lambda obj:
            f'{obj.title} ({obj.price} ₽)'
        )