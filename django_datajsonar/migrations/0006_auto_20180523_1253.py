# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-23 12:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_datajsonar', '0005_auto_20180522_1249'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='readdatajsontask',
            name='catalogs',
        ),
        migrations.RemoveField(
            model_name='readdatajsontask',
            name='stats',
        ),
        migrations.AlterField(
            model_name='readdatajsontask',
            name='logs',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='readdatajsontask',
            name='status',
            field=models.CharField(choices=[('RUNNING', 'Procesando catálogos'), ('FINISHED', 'Finalizada')], max_length=20),
        ),
    ]