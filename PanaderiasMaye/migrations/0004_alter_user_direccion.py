# Generated by Django 4.0.6 on 2025-03-26 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PanaderiasMaye', '0003_alter_user_direccion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='direccion',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
