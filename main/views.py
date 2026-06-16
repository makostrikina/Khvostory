import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .forms import ClientForm, PetForm, DoctorForm, ServiceForm, AppointmentForm, ProvidedServiceForm
from django.shortcuts import render, redirect
from .models import Client, Pet, Doctor, Service, Appointment, ProvidedService, Receipt
from django.db.models import Sum, F, DecimalField
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from django import forms
from django.shortcuts import (render, redirect, get_object_or_404)
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.contrib.auth.models import User

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

def init_admin(request):
    if not User.objects.exists():
        User.objects.create_superuser(
            username='admin',
            password='M1234567'
        )
        return HttpResponse("admin created")
    return HttpResponse("already exists")

def custom_404(request, exception):
    return render(
        request,
        '404.html',
        status=404
    )

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.contrib.auth.models import User

def get_users_api(request):
    """API для получения списка пользователей группы 'Client'"""
    group_name = request.GET.get('group', 'Client')
    users = User.objects.filter(groups__name=group_name).values('id', 'username', 'email')
    return JsonResponse(list(users), safe=False)

def clients_spa(request):
    """SPA версия страницы клиентов"""
    return render(request, 'main/clients_spa.html')

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.groups.filter(name='Admin').exists():
            return HttpResponseForbidden("Нет доступа")

        return view_func(request, *args, **kwargs)

    return wrapper

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

def is_client(user):
    return user.groups.filter(name='Client').exists()

@login_required
def home(request):
    if is_client(request.user):
        client = Client.objects.get(user=request.user)

        appointments = Appointment.objects.filter(client=client)
        pets = Pet.objects.filter(owner=client)

        return render(
            request,
            'main/home.html',
            {
                'appointments': appointments,
                'pets': pets,
                'client_dashboard': True
            }
        )

    elif is_doctor(request.user):
        appointments = Appointment.objects.filter(
            doctor__user=request.user
        )

        return render(
            request,
            'main/home.html',
            {
                'appointments': appointments,
                'doctor_dashboard': True
            }
        )

    else:
        clients_count = Client.objects.count()
        pets_count = Pet.objects.count()
        doctors_count = Doctor.objects.count()
        appointments_count = Appointment.objects.count()
        appointments = Appointment.objects.all()
        latest_appointments = Appointment.objects.order_by(
            '-appointment_date'
        )[:5]

        return render(
            request,
            'main/home.html',
            {
                'clients_count': clients_count,
                'pets_count': pets_count,
                'doctors_count': doctors_count,
                'appointments_count': appointments_count,
                'latest_appointments': latest_appointments,
                'admin_dashboard': True
            }
        )

@login_required
def clients(request):
    query = request.GET.get('q')
    if query:
        clients_list = Client.objects.filter(full_name__icontains=query)
    else:
        clients_list = Client.objects.all()
    
    paginator = Paginator(clients_list, 9)
    page_number = request.GET.get('page')
    clients = paginator.get_page(page_number)
    
    return render(request, 'main/clients.html', {'clients': clients})

@login_required
def pets(request):
    query = request.GET.get('q')

    if query:
        all_pets = Pet.objects.filter(
            Q(name__icontains=query) |
            Q(species__icontains=query) |
            Q(breed__icontains=query) |
            Q(owner__full_name__icontains=query)
        )

    else:
        all_pets = Pet.objects.all()

    paginator = Paginator(
        all_pets,
        4
    )
    page_number = request.GET.get('page')
    pets = paginator.get_page(page_number)

    return render(
        request,
        'main/pets.html',
        {
            'pets': pets,
            'all_pets': all_pets
        }
    )

@login_required
def doctors(request):
    query = request.GET.get('q')

    if query:
        doctors = Doctor.objects.filter(
            Q(full_name__icontains=query) |
            Q(specialization__icontains=query)
        )

    else:
        doctors = Doctor.objects.all()

    return render(
        request,
        'main/doctors.html',
        {
            'doctors': doctors
        }
    )

@login_required
def services(request):
    query = request.GET.get('q')

    if query:
        services = Service.objects.filter(
            Q(title__icontains=query)
        )

    else:
        services = Service.objects.all()

    return render(
        request,
        'main/services.html',
        {
            'services': services
        }
    )

@login_required
def appointments(request):
    date = request.GET.get('date')

    if is_client(request.user):
        client = Client.objects.get(user=request.user)
        appointments = Appointment.objects.filter(client=client)

    elif is_doctor(request.user):
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(doctor=doctor)

    else:
        appointments = Appointment.objects.all()

    if date:
        appointments = appointments.filter(appointment_date=date)

    status = request.GET.get('status')
    if status:
        appointments = appointments.filter(status=status)

    return render(request, 'main/appointments.html', {
        'appointments': appointments,
        'client_dashboard': is_client(request.user)
    })

@login_required
def provided_services(request):
    if is_doctor(request.user):
        doctor = Doctor.objects.get(user=request.user)
        provided_services = ProvidedService.objects.filter(
            appointment__doctor=doctor
        )

    else:
        provided_services = ProvidedService.objects.all()

    return render(request, 'main/provided_services.html', {
        'provided_services': provided_services
    })

@login_required
def receipt(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )

    if is_client(request.user):
        if appointment.client.user != request.user:
            return redirect('home')

    elif is_doctor(request.user):
        if appointment.doctor.user != request.user:
            return redirect('home')

    services = ProvidedService.objects.filter(
        appointment=appointment
    )

    return render(
        request,
        'main/receipt.html',
        {
            'appointment': appointment,
            'services': services
        }
    )

@login_required
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/clients/')
    else:
        form = ClientForm()

    return render(request, 'main/add_client.html', {'form': form})

@login_required
def edit_client(request, client_id):
    client = Client.objects.get(id=client_id)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('/clients/')
    else:
        form = ClientForm(instance=client)

    return render(request, 'main/edit_client.html', {'form': form})

@login_required
@admin_required
def delete_client(request, client_id):
    client = Client.objects.get(id=client_id)
    client.delete()
    return redirect('/clients/')

@login_required
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/pets/')
    else:
        form = PetForm()

    return render(request, 'main/add_pet.html', {'form': form})

@login_required
def edit_pet(request, pet_id):
    pet = Pet.objects.get(id=pet_id)

    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            return redirect('/pets/')
    else:
        form = PetForm(instance=pet)

    return render(request, 'main/edit_pet.html', {'form': form})

@login_required
def delete_pet(request, pet_id):
    pet = Pet.objects.get(id=pet_id)
    pet.delete()
    return redirect('/pets/')

@login_required
@admin_required
def add_doctor(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/doctors/')
    else:
        form = DoctorForm(request.POST or None)

    return render(request, 'main/add_doctor.html', {'form': form})

@login_required
@admin_required
def edit_doctor(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)

    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('/doctors/')
    else:
        form = DoctorForm(instance=doctor)

    return render(request, 'main/edit_doctor.html', {'form': form})

@login_required
@admin_required
def delete_doctor(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    doctor.delete()
    return redirect('/doctors/')

@login_required
@admin_required
def add_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/services/')
    else:
        form = ServiceForm()

    return render(request, 'main/add_service.html', {'form': form})

@login_required
def edit_service(request, service_id):
    service = Service.objects.get(id=service_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('/services/')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'main/edit_service.html', {'form': form})

@login_required
@admin_required
def delete_service(request, service_id):
    service = Service.objects.get(id=service_id)
    service.delete()
    return redirect('/services/')

@login_required
def add_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(
        request.POST or None,
        user=request.user
        )

        if form.is_valid():
            appointment = form.save(commit=False)

            # клиенту автоматически подставляем владельца
            if is_client(request.user):
                appointment.client = Client.objects.get(
                    user=request.user
                )
                # клиент не может менять статус
                appointment.status = 'scheduled'
            appointment.save()

            return redirect('appointments')

    else:
        form = AppointmentForm(user=request.user)

        if is_client(request.user):
            form.fields['client'].widget = forms.HiddenInput()

    return render(request, 'main/add_appointment.html', {
        'form': form
    })

@login_required
def edit_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    
    if is_client(request.user):
        return redirect('appointments')


    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect('/appointments/')
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, 'main/edit_appointment.html', {'form': form})

@login_required
def delete_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.delete()
    return redirect('/appointments/')

@login_required
def add_provided_service(request):
    if request.method == 'POST':
        form = ProvidedServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/provided-services/')
    else:
        form = ProvidedServiceForm()

    return render(request, 'main/add_provided_service.html', {'form': form})

@login_required
def edit_provided_service(request, provided_service_id):
    item = ProvidedService.objects.get(id=provided_service_id)

    if request.method == 'POST':
        form = ProvidedServiceForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('/provided-services/')
    else:
        form = ProvidedServiceForm(instance=item)

    return render(request, 'main/edit_provided_service.html', {'form': form})

@login_required
def delete_provided_service(request, provided_service_id):
    item = ProvidedService.objects.get(id=provided_service_id)
    item.delete()
    return redirect('/provided-services/')

@login_required
def generate_receipt(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    services = ProvidedService.objects.filter(appointment=appointment)

    total_sum = 0
    for item in services:
        total_sum += item.quantity * item.service.price

    Receipt.objects.update_or_create(
        appointment=appointment,
        defaults={'total': total_sum}
    )

    return redirect('/receipts/')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('/')

        else:

            return render(
                request,
                'main/login.html',
                {
                    'error': 'Неверный логин или пароль'
                }
            )

    return render(
        request,
        'main/login.html'
    )

def logout_view(request):
    logout(request)
    return redirect('/login/')

#статистика
@login_required
@admin_required
def pets_chart(request):


    #статусы приемов
    scheduled_count = Appointment.objects.filter(
        status='scheduled'
    ).count()

    completed_count = Appointment.objects.filter(
        status='completed'
    ).count()

    cancelled_count = Appointment.objects.filter(
        status='cancelled'
    ).count()

    #приемы по врачам
    doctors = Doctor.objects.all()

    doctor_names = []

    doctor_counts = []

    for doctor in doctors:

        doctor_names.append(
            doctor.full_name
        )

        count = Appointment.objects.filter(
            doctor=doctor
        ).count()

        doctor_counts.append(count)

    #питомцы по видам
    species_data = Pet.objects.values('species').annotate(total=Count('species'))

    species_labels = []

    species_counts = []

    for item in species_data:
        if item['species']:

            species_labels.append(
                item['species']
            )

            species_counts.append(
                item['total']
            )
    return render(
        request,
        'main/pets_chart.html',
        {

            'scheduled_count': scheduled_count,

            'completed_count': completed_count,

            'cancelled_count': cancelled_count,

            'doctor_names': doctor_names,

            'doctor_counts': doctor_counts,
            'species_labels': species_labels,
            'species_counts': species_counts,

        }
    )

#создаем pdf
@login_required
def receipt_pdf(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )

    if is_client(request.user):
        if appointment.client.user != request.user:
            return redirect('home')

    elif is_doctor(request.user):
        if appointment.doctor.user != request.user:
            return redirect('home')

    services = ProvidedService.objects.filter(
        appointment=appointment
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="receipt.pdf"'

    pdfmetrics.registerFont(
        TTFont(
            'DejaVu',
            'main/static/fonts/DejaVuSans.ttf'
        )
    )

    p = canvas.Canvas(response)

    p.setFont("DejaVu", 16)
    y = 800

    # ---------------- HEADER ----------------
    p.drawString(200, y, "ВЕТЕРИНАРНАЯ КЛИНИКА")
    y -= 30

    p.setFont("DejaVu", 12)
    p.drawString(260, y, "ЧЕК НА ПРИЁМ")
    y -= 40

    # ---------------- INFO ----------------
    p.drawString(80, y, f"Клиент: {appointment.client.full_name}")
    y -= 20

    p.drawString(80, y, f"Питомец: {appointment.pet.name}")
    y -= 20

    p.drawString(80, y, f"Врач: {appointment.doctor.full_name}")
    y -= 20

    p.drawString(80, y, f"Дата: {appointment.appointment_date}")
    y -= 40

    # ---------------- TABLE HEADER ----------------
    p.setFont("DejaVu", 11)

    p.drawString(80, y, "Услуга")
    p.drawString(350, y, "Цена")
    y -= 20

    p.line(80, y, 500, y)
    y -= 20

    # ---------------- SERVICES ----------------
    total = 0

    for item in services:

        p.drawString(80, y, item.service.title)
        p.drawString(350, y, f"{item.service.price} руб.")

        total += item.service.price
        y -= 20

        # если страница закончилась
        if y < 100:
            p.showPage()
            p.setFont("DejaVu", 11)
            y = 800

    # ---------------- TOTAL ----------------
    y -= 30
    p.line(80, y, 500, y)
    y -= 30

    p.setFont("DejaVu", 12)
    p.drawString(80, y, f"ИТОГО: {total} руб.")


    p.showPage()
    p.save()

    return response

#создаем excel экспорт
@login_required
def export_appointments_excel(request):

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = 'Appointments'

    worksheet.append([
        'ID',
        'Client',
        'Pet',
        'Doctor',
        'Date'
    ])

    appointments = Appointment.objects.all()

    for appointment in appointments:

        worksheet.append([

            appointment.id,

            appointment.client.full_name,

            appointment.pet.name,

            appointment.doctor.full_name,

            str(appointment.appointment_date)

        ])

    response = HttpResponse(
        content_type=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = (
        'attachment; filename=appointments.xlsx'
    )

    workbook.save(response)

    return response

#календарь
@login_required
def calendar_view(request):

    if is_client(request.user):
        client = Client.objects.get(user=request.user)
        appointments = Appointment.objects.filter(client=client)

    elif is_doctor(request.user):
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(doctor=doctor)

    else:
        appointments = Appointment.objects.all()

    date = request.GET.get('date')

    if date:
        appointments = appointments.filter(appointment_date=date)

    return render(request, 'main/calendar.html', {
        'appointments': appointments,
        'selected_date': date
    })

#история болезни питомца
@login_required
def pet_history(request, pet_id):

    pet = get_object_or_404(
        Pet,
        id=pet_id
    )

    if is_client(request.user):

        if pet.client.user != request.user:

            return redirect('home')

    appointments = Appointment.objects.filter(
        pet=pet
    ).order_by('-appointment_date')

    return render(
        request,
        'main/pet_history.html',
        {
            'pet': pet,
            'appointments': appointments
        }
    )

@login_required
def pet_detail(request, pet_id):

    pet = get_object_or_404(
        Pet,
        id=pet_id
    )

    return render(
        request,
        'main/pet_detail.html',
        {
            'pet': pet,
            'is_admin': is_admin(request.user)
        }
    )

#отмена приема
@login_required
def cancel_appointment(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )

    if not is_client(request.user):
        return redirect('home')

    if appointment.client.user != request.user:
        return redirect('home')

    appointment.status = 'cancelled'

    appointment.save()

    return redirect('appointments')

@login_required
def receipts(request):
    if is_client(request.user):

        client = Client.objects.get(
            user=request.user
        )

        appointments = Appointment.objects.filter(
            client=client
        )

    elif is_doctor(request.user):

        doctor = Doctor.objects.get(
            user=request.user
        )

        appointments = Appointment.objects.filter(
            doctor=doctor
        )

    else:

        appointments = Appointment.objects.all()

    return render(
        request,
        'main/receipts.html',
        {
            'appointments': appointments
        }
    )