# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reduction_viewer', '0002_auto_20140828_1157'),
        ('reduction_variables', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RunVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=300)),
                ('type', models.CharField(max_length=50)),
                ('reduction_run', models.ForeignKey(to='reduction_viewer.ReductionRun')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
