# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-15 14:59
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Buurt',
            fields=[
                ('id', models.CharField(max_length=14, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=4)),
                ('naam', models.CharField(max_length=40)),
                ('geometrie', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('vakken', models.IntegerField(null=True)),
                ('fiscale_vakken', models.IntegerField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='parkeervak',
            name='buurt',
            field=models.CharField(db_index=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='parkeervak',
            name='point',
            field=django.contrib.gis.db.models.fields.PointField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='wegdeel',
            name='fiscale_vakken',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='wegdeel',
            name='vakken',
            field=models.IntegerField(null=True),
        ),
    ]