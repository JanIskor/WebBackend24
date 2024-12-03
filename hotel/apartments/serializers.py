from rest_framework import serializers
# from argon2 import hash_password
from .models import ApartHotelService, Application, ApplicationApartments
from django.contrib.auth.models import User
from collections import OrderedDict


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
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields
        

class ApplicationApartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationApartments
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "password"]

        # def create(self, validated_data):
        #     user = User.objects.create(
        #         email=validated_data['email'],
        #         username=validated_data['username']
        #     )

        #     user.set_password(validated_data['password'])
        #     user.save()

        #     return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)