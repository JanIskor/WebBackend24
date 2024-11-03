from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

# Create your models here.
class ApartHotelService(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=30, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    image = models.URLField(default='',blank=True, null=True, verbose_name='Фото')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    details = models.TextField(default='There is no detail text', verbose_name='Подробности')
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")

    class Meta:
        db_table = 'aparthotel_service'
        verbose_name = 'Апартамент'
        verbose_name_plural = 'Апартаменты'


class Application(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удалена'),
        ('created', 'Сформирована'),
        ('completed', 'Завершёна'),
        ('rejected', 'Отклонёна')
    ]

    create_date = models.DateTimeField(default=timezone.now, verbose_name='Дата создания заявки')
    update_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата обновления')
    complete_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='заявки_создателя')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='заявки_модератора')

    start_date = models.DateField(default=timezone.now, verbose_name='Дата приезда')
    final_date = models.DateField(default=timezone.now, verbose_name='Дата выезда')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft', verbose_name='Статус заявки')

    class Meta:
        db_table = 'applications'
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
    
    def calculate_total_price(self):
        total = ApplicationApartments.objects.filter(application=self).aggregate(total_price=Sum('aparthotel_service__price'))
        return total['total_price'] if total['total_price'] else 0



class ApplicationApartments(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='Заявка')
    aparthotel_service = models.ForeignKey(ApartHotelService, on_delete=models.CASCADE, related_name='Услуга')
    comments_wishes = models.TextField(default='Введите текст', verbose_name='Комментарии')

    class Meta:
        db_table = 'application_apart_service'
        verbose_name = 'Услуга в апарт-отеле'
        verbose_name_plural = 'Услуги в апарт-отеле'
        constraints = [
            models.UniqueConstraint(fields=['application', 'aparthotel_service'], name='unique_app_apartments')
        ]