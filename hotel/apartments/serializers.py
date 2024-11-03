from rest_framework import serializers
# from argon2 import hash_password
from .models import ApartHotelService, Application, ApplicationApartments
from django.contrib.auth.models import User


# class UserSerializer(serializers.ModelSerializer):
#     application_set = ApplicationSerializer(many=True, read_only=True)
#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = AuthUser
#         fields = ["id", "first_name", "last_name", "username", "email", "password", "application_set"]

#     def create(self, validated_data):
#         # Создаем нового пользователя
#         user = AuthUser(**validated_data)
#         user.password = validated_data['password']
#         user.save()
#         return user

class ApplicationSerializer(serializers.ModelSerializer):
  create_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
  update_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
  complete_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
  start_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
  final_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
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

  # def create(self, validated_data):
  #       user = User.objects.create(
  #           email=validated_data['email'],
  #           username=validated_data['username']
  #       )

  #       user.set_password(validated_data['password'])
  #       user.save()

  #       return user

