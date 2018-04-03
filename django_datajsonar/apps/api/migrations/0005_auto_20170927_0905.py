# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-09-27 13:05
from __future__ import unicode_literals

from django.db import migrations, models
import django_datajsonar.apps.api.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_distribution_data_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distribution',
            name='data_file',
            field=models.FileField(blank=True, max_length=2000, upload_to=django_datajsonar.apps.api.models.filepath),
        ),
    ]
