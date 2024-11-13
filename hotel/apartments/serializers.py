from rest_framework import serializers
# from argon2 import hash_password
from .models import ApartHotelService, Application, ApplicationApartments
from django.contrib.auth.models import User


class ApplicationSerializer(serializers.ModelSerializer):
  create_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
  update_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
  complete_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
  start_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
  final_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
  creator = serializers.StringRelatedField()
  moderator = serializers.StringRelatedField()
  class Meta:
      model = Application
      fields = [
                  'id', 'create_date', 'update_date', 
                  'complete_date', 'creator', 'moderator', 'start_date', 
                  'final_date', 'total_price', 'status'
          ]
        

class ApartHotelServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartHotelService
        fields = [
                    'id', 'name', 'description', 'image', 
                    'price', 'details'
            ]
        

class ApplicationApartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationApartments
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "password", "is_staff", "is_superuser"]


