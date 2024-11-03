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


urlpatterns = [
    path("admin/", admin.site.urls), 
    path('', views.index_apart_hotel, name="index_apart_hotel"),
    path("application_apartments_detail/<int:application_id>", views.application_apartments_detail, name="application_apartments_detail"), 
    path('apartments/<int:id_apartments>/', views.apartments_detail, name='apartments_detail'),
    path('apartments/addService/<int:id_apartments>/', views.addService, name='addService'),
    path('apartments/deleteService/<int:id>/', views.deleteService, name='deleteService'),


    # Набор методов для услуг
    path('api/apart_services/', ApartHotelServiceList.as_view(), name='apart-detail'),
    path('api/apart_service/<int:id_apartments>/', ApartHotelServiceDetail.as_view(), name='apart-detail'),
    path('api/apart_service/<int:id_apartments>/add-draft/', ApartHotelServiceDetail.as_view(), name='apart-detail-draft'),
    path('api/apart_service/<int:pk>/edit/', ApartHotelServiceEditingView.as_view(), name='apart-detail'),

    # Набор методов для заявок
    path('api/application/', search_application),  # GET
    path('applications/<int:pk>/', views.ApplicationDetail.as_view(), name='apps-detail'),
    path('applications/<int:pk>/submit/', views.ApplicationFormingView.as_view(), name='apps-detail'),
    path('applications/<int:pk>/accept-reject/', views.ApplicationCompletingView.as_view(), name='apps-detail'),

    # Набор методов для M:M
    path('apart_service_map/', views.ApplicationApartmentsList.as_view(), name="map-list"),
    path('apart_service_map/<int:pk>/', views.ApplicationApartmentsDetail.as_view(), name="map-detail"),
    
    # Набор методов для пользователей
	path('users/', views.UsersList.as_view(), name='users-list'),
	path('user/<int:pk>/', views.UserDetail.as_view(), name='user'),
	path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', logout), # POST
]
