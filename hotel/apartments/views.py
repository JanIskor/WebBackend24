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

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from .serializers import ApplicationSerializer, ApartHotelServiceSerializer, ApplicationApartmentsSerializer, UserSerializer

from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, authentication_classes
from .permissions import *
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import uuid
import redis

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

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


def get_draft_application():
    return Application.objects.filter(status="draft").first()


def get_user():
    return User.objects.filter(is_superuser=False).first()


def get_moderator():
    return User.objects.filter(is_superuser=True).first()





class ApplicationList(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    authentication_classes = [AuthBySessionID]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить информацию о списке заявок"
    )
    def get(self, request, format=None):
        start_date = request.query_params.get('date_formation_start', None)
        end_date = request.query_params.get('date_formation_end', None)
        status_ = request.query_params.get('status')
        if request.user.is_staff:
            object_list = self.model_class.objects.exclude(status__in=["draft", "rejected"])
        else:
            object_list = self.model_class.objects.filter(creator=request.user).exclude(status__in=['deleted', 'draft'])
        if status_:
            object_list = object_list.filter(status=status_)

        serializer = self.serializer_class(object_list, many=True)
        return Response(serializer.data)

class UserViewSet(ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model_class = User

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request username ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(username=serializer.data['username'],
                                                 password=serializer.data['password'],
                                                 is_staff=serializer.data['is_staff'],
                                                 is_superuser=serializer.data['is_superuser'])

            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Exist', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

# ////////////
class ApplicationApartmentsList(APIView):
    model_class = ApplicationApartments
    serializer_class = ApplicationApartmentsSerializer
    @swagger_auto_schema(
        operation_summary="Получить данные о бронировании"
    )
    def get(self, request, format=None):
        apps_apart = self.model_class.objects.all()
        serializer = self.serializer_class(apps_apart, many=True)
        return Response(serializer.data)
        
class ApplicationApartmentsDetail(APIView):
    model_class = ApplicationApartments
    serializer_class = ApplicationApartmentsSerializer

    @swagger_auto_schema(
        operation_summary="Получить данные о бронировании по ID"
    )
    def get(self, request, pk, format=None):
        apart_hotel_service = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(apart_hotel_service)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ApplicationApartmentsSerializer,
        operation_summary="Изменить данные о бронировании"
    )
    def put(self, request, pk, format=None):
        app_apart = get_object_or_404(self.model_class, pk=pk)
        if Application.objects.get(id=app_apart.application_id).status == 'draft':
            updated_data = {key: value for key, value in request.data.items() if key in ['comments_wishes']}
            serializer = self.serializer_class(app_apart, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# //////////////////////////
class ApartHotelServiceList(APIView):
    model_class = ApartHotelService
    serializer_class = ApartHotelServiceSerializer
    @swagger_auto_schema(
        operation_summary="Получить список услуг апарт-отеля"
    )
    def get(self, request, format=None):
        apart_hotel_service = self.model_class.objects.filter(status=1).order_by('price')
        serializer = self.serializer_class(apart_hotel_service, many=True)
        user_draft_apps = Application.objects.filter(status='draft')
        if user_draft_apps.exists():
            draft_app_id = user_draft_apps.first().id
            quantity = ApplicationApartments.objects.filter(application_id=draft_app_id).count()

        else:
            draft_app_id = None
            quantity = 0
        return Response(
            {'draft_app_id': draft_app_id, 'number_of_services': quantity, 'services': serializer.data})
    @swagger_auto_schema(
        request_body=ApartHotelServiceSerializer,
        operation_summary="Создать новую услугу апарт-отеля"
    )
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_apart_service = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApartHotelServiceDetail(APIView):
    model_class = ApartHotelService
    model_class2 = Application
    model_class3 = ApplicationApartments
    serializer_class = ApartHotelServiceSerializer
    @swagger_auto_schema(   
        operation_summary="Посмотреть услугу апарт-отеля"
    )
    def get(self, request, id_apartments, format=None):
        apart_hotel_service = get_object_or_404(self.model_class, id=id_apartments)
        serializer = self.serializer_class(apart_hotel_service)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ApartHotelServiceSerializer,
        operation_summary="Изменить услугу апарт-отеля"
    )
    # Обновляет информацию об услугах в апарт-отеле (для модератора)
    def put(self, request, id_apartments, format=None):
        apart_hotel_service = get_object_or_404(self.model_class, id=id_apartments)
        serializer = self.serializer_class(apart_hotel_service, data=request.data, partial=True)
        if 'pic' in serializer.initial_data:
            pic_result = add_pic(apart_hotel_service, serializer.initial_data['pic'])
            if 'error' in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save(creator=get_user())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(   
        operation_summary="Удалить услугу апарт-отеля"
    )
    # Удаляет информацию об услугах в апарт-отеле 
    def delete(self, request, id_apartments, format=None):
        apart_hotel_service = get_object_or_404(self.model_class, id=id_apartments)
        apart_hotel_service.delete()
        delete_pic(id_apartments)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=ApartHotelServiceSerializer,
        operation_summary="Добавить услугу в заявку"
    )
    def post(self, request, id_apartments):
            try:
                mock_user = get_user()  # Используем внешнюю функцию
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            apart_service = get_object_or_404(self.model_class, id=id_apartments)
            current_application, created = Application.objects.get_or_create(creator=mock_user, status='draft')
            if not ApplicationApartments.objects.filter(aparthotel_service=apart_service, application=current_application).exists():
                created_application_apart_service = ApplicationApartments.objects.create(
                    application=current_application,
                    aparthotel_service=apart_service,
                    comments_wishes="New", 
                    )            
            else:
                return Response({'error': 'Услуга уже добавлена в данную заявку'}, status=status.HTTP_400_BAD_REQUEST)
            
            current_application.save()
            created_application_apart_service.save()

            application_serializer = ApplicationSerializer(current_application).data

            return Response(
                    {
                        'message':'Услуга добавлена в черновик',
                        'apart_application': application_serializer,
                    },
                    status=status.HTTP_201_CREATED
                )

# /////////////////////////
class ApplicationDetail(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    serializer_class2 = ApartHotelServiceSerializer

    @swagger_auto_schema(
        operation_summary="Посмотреть заявку"
    )
    def get(self, request, pk, format=None):
        application = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(application)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ApplicationSerializer,
        operation_summary="Изменить заявку"
    )
    # Обновляет доп поля заявки
    def put(self, request, pk, format=None):
        application = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(application, data=request.data, partial=True)  # partial=True для частичного обновления
        
        if serializer.is_valid():
            serializer.save()  # Сохраняем изменения
            return Response(serializer.data, status=status.HTTP_200_OK)  # Возвращаем обновленные данные
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Если есть ошибки валидации

    @swagger_auto_schema(
        operation_summary="Удалить заявку"
    )
    def delete(self, request, pk, format=None):
        # Получаем конфигурацию по id
        application = get_object_or_404(self.model_class, pk=pk)

        application.status = 'deleted'
        application.save()

        return Response({"message": "Статус обновлен на удален"}, status=status.HTTP_200_OK)



# ///////////////////////////
class ApplicationFormingView(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer

    @swagger_auto_schema(
        operation_summary="Посмотреть заявку"
    )
    def get(self, request, pk, format=None):
        application = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(application)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ApplicationSerializer,
        operation_summary="Сформировать заявку, обновив её статус на 'Сформирована'"
    )
    def put(self, request, pk, format=None):
        user_instance = get_user()

        # Проверяем, является ли текущий пользователь модератором
        # if not user_instance.is_staff:
        #     return Response({'error': 'Текущий пользователь не является модератором'}, status=status.HTTP_403_FORBIDDEN)

        application = get_object_or_404(Application, pk=pk)

        # Проверяем, что заявка имеет статус "Сформирована"
        if application.status != 'draft':
            return Response({'error': 'Заявка может быть сформирована только в статусе "Черновик"'}, status=status.HTTP_403_FORBIDDEN)

        # Устанавливаем новый статус заявки
        application.status = 'created'
        application.moderator = user_instance  # Устанавливаем текущего пользователя как модератора
        application.update_date = timezone.now()  # Устанавливаем дату изменения

        application.save()

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

# /////////////////////////
class ApplicationCompletingView(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    permission_classes = [IsManager]
    authentication_classes = [AuthBySessionID]

    @swagger_auto_schema(
        operation_summary="Посмотреть заявку"
    )
    def get(self, request, pk, format=None):
        application = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(application)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ApplicationSerializer,
        operation_summary="Завершить или отклонить заявку, обновив её статус"
    )
    def put(self, request, pk, format=None):
        # user_instance = get_user()
        application = get_object_or_404(Application, pk=pk)
        if request.user.id != application.creator_id:
            application.moderator_id = request.user.id
            print(request.user.id)
        # Проверяем, является ли текущий пользователь модератором
        if not user_instance.is_staff:
            return Response({'error': 'Текущий пользователь не является модератором'}, status=status.HTTP_403_FORBIDDEN)

            # Проверяем, что заявка имеет статус "Сформирована"
            if application.status != 'created':
                return Response({'error': 'Заявка может быть завершена или отклонена только в статусе "Сформирована"'}, status=status.HTTP_403_FORBIDDEN)

            # Проверяем, что в запросе передан статус
            new_status = request.data.get('status')
            if new_status not in ['completed', 'rejected']:
                return Response({'error': 'Недопустимый статус. Ожидался статус "Завершёна" или "Отклонёна"'}, status=status.HTTP_400_BAD_REQUEST)

            # Устанавливаем новый статус заявки
            application.status = new_status
            application.moderator = user_instance  # Устанавливаем текущего пользователя как модератора
            application.completed_at = timezone.now()  # Устанавливаем дату завершения

            total_price = application.calculate_total_price()  # Предполагается, что этот метод возвращает сумму
            application.total_price = total_price 
            application.save()

            serializer = ApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(request.user)
        return Response({'error': "Permissiod denied. Is creator!"}, status=status.HTTP_403_FORBIDDEN)
# /////////////////////////////
class ApartHotelServiceEditingView(APIView):
    model_class = ApartHotelService
    serializer_class = ApartHotelServiceSerializer

    @swagger_auto_schema(
        request_body=ApartHotelServiceSerializer,
        operation_summary="Изменить информацию об услуге"
    )
    # Обновляет информацию об элементе
    def put(self, request, pk, format=None):
        apart_service = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(apart_service, data=request.data, partial=True)
        # Изменение фото 
        if 'pic' in serializer.initial_data:
            pic_result = add_pic(apart_service, serializer.initial_data['pic'])
            if 'error' in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=ApartHotelServiceSerializer,
        operation_summary="Заменить фотографию"
    )
    # Заменяет картинку, удаляя предыдущую
    def post(self, request, pk, format=None):
        apart_service = get_object_or_404(self.model_class, pk=pk)

        # Проверяем наличие нового изображения
        if 'pic' in request.data:
            # Удаляем старое изображение, если оно существует
            if apart_service.image:
                delete_result = delete_pic(apart_service.image.split("/")[-1])  # Удаляем изображение по имени
                if 'error' in delete_result:
                    return Response(delete_result, status=status.HTTP_400_BAD_REQUEST)

            # Загружаем новое изображение
            pic_result = add_pic(apart_service, request.data['pic'])
            if 'error' in pic_result.data:
                return pic_result

        return Response({"message": "Изображение успешно обновлено"}, status=status.HTTP_200_OK)
   
# ///////////////////////
class UsersList(APIView):
    model_class = User
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_summary="Получить список пользователей"
    )
    def get(self, request, format=None):
        user = self.model_class.objects.all()
        serializer = self.serializer_class(user, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserSerializer,
        operation_summary="Создать нового пользователя"
    )
    def post(self, request, format=None):
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(username=serializer.data['username'],
                                                 password=serializer.data['password'],
                                                 is_staff=serializer.data['is_staff'],
                                                 is_superuser=serializer.data['is_superuser'])

            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Exist', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    model_class = User
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_summary="Получить информацию о пользователе"
    )
    def get(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserSerializer,
        operation_summary="Изменить информацию о пользователе"
    )
    def put(self, request, pk, format=None):
        # Получаем пользователя по id
        user = get_object_or_404(self.model_class, pk=pk)

        # Сериализуем данные с обновлением
        serializer = self.serializer_class(user, data=request.data, partial=True)

        if serializer.is_valid():
            # Если пароль изменен, хешируем его
            password = serializer.validated_data.get('password')
            if password:
                serializer.validated_data['password'] = make_password(password)

            # Сохраняем обновленные данные
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_summary="Удалить бронирование"
)
@api_view(['DELETE'])
def delete_apart_service_from_application(request, application_id, id_apartments):
    application = get_object_or_404(Application, id=application_id)

    if application.status == 'deleted':
        return Response({'error': 'Заявление удалено, нельзя удалить услугу'}, status=status.HTTP_400_BAD_REQUEST)

    aparthotel_service = get_object_or_404(ApartHotelService, id=id_apartments)
    apart_service_to_application = ApplicationApartments.objects.filter(aparthotel_service=aparthotel_service, application=application).first()

    if apart_service_to_application:
        apart_service_to_application.delete()
        return Response({'message': 'Услуга в апарт-отеле успешно удалена из заявок'}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'error': 'Услуга не найдена в заявке'}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='post', request_body=UserSerializer, operation_summary="Аутентификация")
@api_view(['Post'])
def login_view(request): 
    # username = request.data["username"]  # допустим передали username и password
    # password = request.data["password"]
    username = request.data.get('username')  # допустим передали username и password
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    print(username, password)
    # if user is not None:
    #     login(request, user)
    #     return HttpResponse("{'status': 'ok'}")
    # else:
    #     return HttpResponse("{'status': 'error', 'error': 'login failed'}")
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        login(request, user)
        return Response({"message": "Вход успешен."}, status=status.HTTP_200_OK)
    return Response({"error": "Неверные данные."}, status=status.HTTP_401_UNAUTHORIZED)



def logout_view(request):
    logout(request._request)
    return Response({'status': 'Success'})



