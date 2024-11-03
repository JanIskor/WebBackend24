from django.contrib import admin

from .models import ApartHotelService, Application, ApplicationApartments

admin.site.register(ApartHotelService)
admin.site.register(Application)
admin.site.register(ApplicationApartments)
# Register your models here.
