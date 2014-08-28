# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reduction_viewer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstrumentVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_run', models.IntegerField()),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=300)),
                ('type', models.CharField(max_length=50)),
                ('instrument', models.ForeignKey(to='reduction_viewer.Instrument')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScriptFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('script', models.BinaryField()),
                ('file_name', models.CharField(max_length=50)),
                ('reduction_run', models.ForeignKey(related_name=b'scripts', to='reduction_viewer.ReductionRun')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
