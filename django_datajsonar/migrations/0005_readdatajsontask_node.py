# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-04 14:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_datajsonar', '0004_auto_20190401_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='readdatajsontask',
            name='node',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_datajsonar.Node'),
        ),
    ]
