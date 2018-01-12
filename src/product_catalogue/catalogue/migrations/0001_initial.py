# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('category_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('content', models.TextField(verbose_name='Content Description')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('category', models.ManyToManyField(blank=True, to='catalogue.Category')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
