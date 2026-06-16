from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from .models import Client
from .forms import ClientForm


def clients_api(request):
    """API для получения списка клиентов"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if query:
        clients_list = Client.objects.filter(full_name__icontains=query)
    else:
        clients_list = Client.objects.all()
    
    paginator = Paginator(clients_list, 9)
    clients_page = paginator.get_page(page)
    
    data = {
        'clients': [
            {
                'id': client.id,
                'full_name': client.full_name,
                'phone': client.phone,
                'email': client.email,
                'user_id': client.user_id
            }
            for client in clients_page
        ],
        'pagination': {
            'current_page': clients_page.number,
            'total_pages': paginator.num_pages,
            'has_previous': clients_page.has_previous(),
            'has_next': clients_page.has_next(),
            'previous_page': clients_page.previous_page_number() if clients_page.has_previous() else None,
            'next_page': clients_page.next_page_number() if clients_page.has_next() else None
        }
    }
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_client_api(request):
    """API для добавления клиента"""
    try:
        data = json.loads(request.body)
        form = ClientForm(data)
        
        if form.is_valid():
            client = form.save()
            return JsonResponse({
                'success': True,
                'client': {
                    'id': client.id,
                    'full_name': client.full_name,
                    'phone': client.phone,
                    'email': client.email,
                    'user_id': client.user_id
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def edit_client_api(request, client_id):
    """API для редактирования клиента"""
    try:
        client = Client.objects.get(id=client_id)
        data = json.loads(request.body)
        form = ClientForm(data, instance=client)
        
        if form.is_valid():
            client = form.save()
            return JsonResponse({
                'success': True,
                'client': {
                    'id': client.id,
                    'full_name': client.full_name,
                    'phone': client.phone,
                    'email': client.email,
                    'user_id': client.user_id
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_client_api(request, client_id):
    """API для удаления клиента"""
    try:
        client = Client.objects.get(id=client_id)
        client.delete()
        return JsonResponse({'success': True})
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)