# Generated by Django 4.2.16 on 2024-10-31 22:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apartments", "0002_aparthotelservice_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aparthotelservice",
            name="image",
            field=models.CharField(
                blank=True, max_length=40, null=True, verbose_name="Фото"
            ),
        ),
    ]
