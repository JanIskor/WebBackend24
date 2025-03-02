from rest_framework import serializers
# from argon2 import hash_password
from .models import ApartHotelService, Application, ApplicationApartments
from django.contrib.auth.models import User
from collections import OrderedDict

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
    def to_representation(self, value):
        serializer = self.parent.apart_service.__class__(value, context=self.context)
        return serializer.data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password", "is_staff", "is_superuser"]

class ApplicationSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    update_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
    complete_date = serializers.DateTimeField(format='%Y-%m-%d', allow_null=True, required=False)
    start_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
    final_date = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
    # creator = serializers.EmailField(source='user.username', read_only=True)
    creator = serializers.StringRelatedField()
    moderator = serializers.StringRelatedField()
    apart_service = ApartHotelServiceSerializer()
    class Meta:
        model = Application
        fields = [
                    'id', 'create_date', 'update_date', 
                    'complete_date', 'creator', 'moderator', 'start_date', 
                    'final_date', 'total_price', 'status', 'apart_service'
            ]
    #     def get_fields(self):
    #         new_fields = OrderedDict()
    #         for name, field in super().get_fields().items():
    #             field.required = False
    #             new_fields[name] = field
    #         return new_fields
        
    # def get_moderator(self, obj):
    #     return obj.moderator.username if obj.moderator else None


