# Generated by Django 2.2.16 on 2022-11-03 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='confirmation_code',
            field=models.IntegerField(blank=True, default=1, verbose_name='Код подтверждения'),
            preserve_default=False,
        ),
    ]