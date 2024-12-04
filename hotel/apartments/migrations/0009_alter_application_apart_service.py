# Generated by Django 4.2.16 on 2024-12-04 07:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("apartments", "0008_alter_application_apart_service"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="apart_service",
            field=models.ForeignKey(
                blank=True,
                default=0,
                null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                related_name="apart_services",
                to="apartments.application",
                verbose_name="Услуги апарт-отеля",
            ),
        ),
    ]
