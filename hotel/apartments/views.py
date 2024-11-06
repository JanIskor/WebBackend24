from django.shortcuts import render, get_object_or_404, redirect
from datetime import date
from .models import ApartHotelService, Application, ApplicationApartments
from django.db import connection
from django.http import HttpResponseForbidden
from django.http import Http404
from datetime import timezone
from django.utils import timezone 
from django.conf import settings

from django.contrib.auth.hashers import make_password
from .minio import *
from django.contrib.auth.models import User
from rest_framework.decorators import api_view

from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from .serializers import ApplicationSerializer, ApartHotelServiceSerializer, ApplicationApartmentsSerializer, UserSerializer

applications = [
    {
        "id": 1,
        "from": "12.12.2024",
        "duration": '7 дней/ночей',
        "hotel_services": [2, 5, 6],
    },
    {
        "id": 2,
        "from": "15.12.2024",
        "duration": '10 дней/ночей',
        "hotel_services": [2, 4, 5, 6],
    },
    {
        "id": 3,
        "from": "17.12.2024",
        "duration": '12 дней/ночей',
        "hotel_services": [3, 6],
    }
]
card_apartments = [
  {
        'id': 1,
        'name': 'GRIFFIN SUITE',
        'description': 'Апартаменты для пар',
        'image': 'http://127.0.0.1:9000/hotel/images/1.png',
        'price': '17,388₽',
        'details': "Полулюкс, 1 большая двуспальная кровать, Диван-кровать, Мини-холодильник, 59 кв.м., Гостиная/зона отдыха, Беспроводной доступ в Интернет (платно), Проводной доступ в Интернет (платно), Кофеварка/чайник",
    },
    {
        'id': 2,
        'name': 'STUDIO SUITE',
        'description': 'Семейные апартаменты',
        'image': 'http://127.0.0.1:9000/hotel/images/2.png',
        'price': '21,999₽',
        'details': 'Люкс-студио, 1 кровать размера "king-size", диван-кровать, мини-холодильник, 756 кв. футов/68 кв.м., гостиная/гостиная, обеденная зона, беспроводной интернет, за плату, проводной интернет, за плату, кофеварка/чайник',
    },
    {
        'id': 3,
        'name': 'JUNIOR SUITE',
        'description': 'Гостевые апартаменты',
        'image': 'http://127.0.0.1:9000/hotel/images/3.png',
        'price': '25,768₽',
        'details': 'Представительский большой номер для гостей, 1 кровать размера "king-size", мини-холодильник, 525 кв. футов/47 кв.м., беспроводной интернет, за плату, проводной интернет, за плату, кофеварка/чайник',
    },
       {
        'id': 4,
        'name': 'Парковка в апарт-отеле',
        'description': 'Лучшая парковка в гараже',
        'image': 'http://127.0.0.1:9000/hotel/images/4.png',
        'price': '3,999₽/сутки',
        'details': "Паркинг расположен на закрытой территории гостиницы и оснащен видеонаблюдением, рассчитан на 150 мест, включая места не только для легковых автомобилей, а также для крупногабаритного транспорта, например,  туристических автобусов.",
    },
    {
        'id': 5,
        'name': 'Завтрак в номер',
        'description': 'Восхитительный завтрак по утрам',
        'image': 'http://127.0.0.1:9000/hotel/images/5.png',
        'price': '1,999₽',
        'details': "Континентальный завтрак предполагает порционное питание, в которое обычно входят жареные яйца, бекон либо отварные сосиски, тосты, круассаны, овощи, чай или кофе – на выбор. В этом формате ассортимент уже.",
    },
    {
        'id': 6,
        'name': 'SPA процедуры',
        'description': 'Расслабление и удовольствие',
        'image': 'http://127.0.0.1:9000/hotel/images/6.png',
        'price': '3,299₽',
        'details': "Комплексные расслабляющие процедуры, направленные на оздоровление, расслабление и лечение организма человека, его перезагрузку и профилактику многих заболеваний и проблем. Эффект после спа оказывается как на духовном, так и на физическом уровне.",
    },
]
def index_apart_hotel(request):
    
    apartment_name = request.GET.get('apartment_name', '')
    app = Application.objects.filter(status='draft')

    current_application = None

    if request.user.is_authenticated:
        
        current_application = Application.objects.filter(creator=request.user, status='draft').first()
    
    return render(request, 'apartments/hotel_menu.html', {
        'application': app,
        'apartments': ApartHotelService.objects.filter(name__icontains=apartment_name).order_by('price'),
        # 'counter_apart':counter_apart,
        'counter': counter(request),
        'application_id': current_application.id if current_application else None,
    })

def counter(request):
    application = Application.objects.filter(creator=request.user, status='draft').first()
    if application:
        return ApplicationApartments.objects.filter(application=application.id).count()
    else:
        return 0

def apartments_detail(request, id_apartments):

    apartments= get_object_or_404(ApartHotelService, id=id_apartments)

    return render(request, 'apartments/hotel_description.html', {'apartments': apartments})


def application_apartments_detail(request, application_id):
    deleted_apps = Application.objects.filter(status='deleted')
    for a in deleted_apps:
        if application_id == a.id:
            return render(request, 'apartments/deleted.html', {'object': 'заявка'})
    
    selected_apartment_application = get_object_or_404(Application, id=application_id, creator=request.user)

    apartments_application = ApplicationApartments.objects.filter(application=selected_apartment_application)


    if selected_apartment_application.status == 'deleted' :
        raise Http404("Заявок нет")
    

    elif not apartments_application.exists():
        return render(request, 'apartments/hotel_application.html', {
        'apartments_application':  selected_apartment_application,
        'apartments_in_application': None,
        'apartments_application':None,
        })
    
    apartments_in_application=[apartment_application.aparthotel_service for apartment_application in apartments_application ]
    
    return render(request, 'apartments/hotel_application.html', {
        'apartments_in_application': apartments_in_application,
        "from": Application.objects.get(id=application_id).start_date,
        "to": Application.objects.get(id=application_id).final_date,
        "total_price": Application.objects.get(id=application_id).total_price,
        'apartments_application': ordered(application_id),
        'application_id': selected_apartment_application.id,
        'application_amount': calculate_total_price(selected_apartment_application),
    })

def ordered(application_id):
    chosen = ApplicationApartments.objects.filter(application_id=application_id)
    chosen_ids = []
    for c in chosen:
        chosen_ids.append(c.aparthotel_service_id)
    return ApartHotelService.objects.filter(id__in=chosen_ids)

def addService(request, id_apartments):
    if request.method == 'POST':
        apart_hotel_service = get_object_or_404(ApartHotelService, id=id_apartments)
        application, new_application = Application.objects.get_or_create(creator=request.user, status='draft')
        if application:
            ApplicationApartments.objects.update_or_create(application_id=application.id, aparthotel_service_id=apart_hotel_service.id)
        else:
            ApplicationApartments.objects.create(application=new_application.id, aparthotel_service=aparthotel_service.id)
        return redirect('index_apart_hotel')
    return HttpResponseForbidden()

def deleteService(request, id):
    if request.method == 'POST':
        # Подсчитываем сумму услуг в апарт-отеле перед удалением
        total_price = calculate_total_price(id)
        
        # Обновляем статус услуг в апарт-отеле на удаленный
        with connection.cursor() as cursor:
            cursor.execute("UPDATE applications SET status = 'deleted', total_price = %s WHERE id = %s", [total_price, id])
            print(f"Услуга апарт-отеля была удалена. Общая сумма: {{total_price}}")
        
        return redirect('index_apart_hotel')
    else:
        return HttpResponseForbidden()

def calculate_total_price(application_id):
    elements = ApplicationApartments.objects.filter(application_id=application_id)
    
    total_sum = 0

    # Суммируем цены услуг в апарт-отеле
    for el in elements:
        element = ApartHotelService.objects.get(id=el.aparthotel_service_id)
        total_sum += element.price

    return total_sum


