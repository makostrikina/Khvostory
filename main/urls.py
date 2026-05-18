from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('clients/', views.clients, name='clients'),
    path('pets/', views.pets, name='pets'),
    path('doctors/', views.doctors, name='doctors'),
    path('services/', views.services, name='services'),
    path('appointments/', views.appointments, name='appointments'),
    path('provided-services/', views.provided_services, name='provided_services'),
    #path('receipts/', views.receipts, name='receipts'),
    path('add-client/', views.add_client, name='add_client'),
    path('edit-client/<int:client_id>/', views.edit_client),
    path('delete-client/<int:client_id>/', views.delete_client),
    path('add-pet/', views.add_pet, name='add_pet'),
    path('edit-pet/<int:pet_id>/', views.edit_pet),
    path('delete-pet/<int:pet_id>/', views.delete_pet),
    path('add-doctor/', views.add_doctor, name='add_doctor'),
    path('edit-doctor/<int:doctor_id>/', views.edit_doctor),
    path('delete-doctor/<int:doctor_id>/', views.delete_doctor),
    path('add-service/', views.add_service, name='add_service'),
    path('edit-service/<int:service_id>/', views.edit_service),
    path('delete-service/<int:service_id>/', views.delete_service),
    path('add-appointment/', views.add_appointment, name='add_appointment'),
    path('edit-appointment/<int:appointment_id>/', views.edit_appointment),
    path('delete-appointment/<int:appointment_id>/', views.delete_appointment),
    path('add-provided-service/', views.add_provided_service, name='add_provided_service'),
    path('edit-provided-service/<int:provided_service_id>/', views.edit_provided_service),
    path('delete-provided-service/<int:provided_service_id>/', views.delete_provided_service),
    path('generate-receipt/<int:appointment_id>/', views.generate_receipt, name='generate_receipt'),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('pets-chart/', views.pets_chart, name='pets_chart'),
    path('receipt-pdf/<int:appointment_id>/', views.receipt_pdf, name='receipt_pdf'),
    path('export-appointments-excel/', views.export_appointments_excel, name='export_appointments_excel'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('pet-history/<int:pet_id>/', views.pet_history, name='pet_history'),
    path('receipt/<int:appointment_id>/', views.receipt, name='receipt'),
    path('pet/<int:pet_id>/', views.pet_detail, name='pet_detail'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('receipts/', views.receipts, name='receipts'),
    path('init-admin/', views.init_admin)
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

handler404 = 'main.views.custom_404'