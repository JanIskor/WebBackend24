"""
URL configuration for hotel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from apartments.views import *
from apartments import views

from django.urls import include, path
from rest_framework import permissions
from django.urls import path, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework import routers
router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("admin/", admin.site.urls), 
    path('', views.index_apart_hotel, name="index_apart_hotel"),
    path("application_apartments_detail/<int:application_id>", views.application_apartments_detail, name="application_apartments_detail"), 
    path('apartments/<int:id_apartments>/', views.apartments_detail, name='apartments_detail'),
    path('apartments/addService/<int:id_apartments>/', views.addService, name='addService'),
    path('apartments/deleteService/<int:id>/', views.deleteService, name='deleteService'),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/', include(router.urls)),


    # Набор методов для услуг
    path('api/apart_services/', ApartHotelServiceList.as_view(), name='apart-detail'),
    path('api/apart_service/<int:id_apartments>/', ApartHotelServiceDetail.as_view(), name='apart-detail'),
    path('api/apart_service/<int:id_apartments>/add-draft/', ApartHotelServiceDetail.as_view(), name='apart-detail-draft'),
    path('api/apart_service/<int:pk>/edit/', ApartHotelServiceEditingView.as_view(), name='apart-detail'),

    # Набор методов для заявок
    path('applications/', views.ApplicationList.as_view(), name='apps-detail'),
    path('applications/<int:pk>/', views.ApplicationDetail.as_view(), name='apps-detail'),
    path('applications/<int:pk>/submit/', views.ApplicationFormingView.as_view(), name='apps-detail'),
    path('applications/<int:pk>/accept-reject/', views.ApplicationCompletingView.as_view(), name='apps-detail'),

    # Набор методов для M:M
    path('apart_service_map/', views.ApplicationApartmentsList.as_view(), name="map-list"),
    path('apart_service_map/<int:pk>/', views.ApplicationApartmentsDetail.as_view(), name="map-detail"),
    path('apart_service_map/<int:application_id>/delete/<int:id_apartments>/', delete_apart_service_from_application, name="map-detail"),

    # Набор методов для пользователей
	path('users/', views.UsersList.as_view(), name='users-list'),
	path('user/<int:pk>/', views.UserDetail.as_view(), name='user'),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
