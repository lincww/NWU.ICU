# Generated by Django 3.1.5 on 2021-01-17 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20210116_2254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='cookie',
            field=models.BinaryField(),
        ),
    ]
