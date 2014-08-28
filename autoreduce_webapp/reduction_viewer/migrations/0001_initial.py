# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import autoreduce_webapp.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_path', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference_number', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('scientists', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('severity', models.CharField(default=1, max_length=1, choices=[(1, b'info'), (2, b'warning'), (3, b'error')])),
                ('is_staff_only', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReductionLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_path', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReductionRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('run_number', models.IntegerField()),
                ('run_name', models.CharField(max_length=50)),
                ('run_version', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('started_by', models.IntegerField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('started', models.DateTimeField()),
                ('finished', models.DateTimeField()),
                ('message', models.CharField(max_length=255)),
                ('graph', autoreduce_webapp.utils.SeparatedValuesField()),
                ('experiment', models.ForeignKey(to='reduction_viewer.Experiment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=25)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='reductionrun',
            name='status',
            field=models.ForeignKey(related_name=b'+', default=1, to='reduction_viewer.Status'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reductionlocation',
            name='reduction_run',
            field=models.ForeignKey(related_name=b'reduction_location', to='reduction_viewer.ReductionRun'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datalocation',
            name='reduction_run',
            field=models.ForeignKey(related_name=b'data_location', to='reduction_viewer.ReductionRun'),
            preserve_default=True,
        ),
    ]
