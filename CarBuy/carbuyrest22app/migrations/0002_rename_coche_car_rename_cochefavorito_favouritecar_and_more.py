# Generated by Django 4.2.7 on 2024-05-21 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carbuyrest22app', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Coche',
            new_name='Car',
        ),
        migrations.RenameModel(
            old_name='CocheFavorito',
            new_name='FavouriteCar',
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(default=123456789, max_length=15),
            preserve_default=False,
        ),
    ]
