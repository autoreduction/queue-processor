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
                ('is_advanced', models.BooleanField(default=False)),
                ('instrument', models.ForeignKey(to='reduction_viewer.Instrument')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RunVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=300)),
                ('type', models.CharField(max_length=50)),
                ('is_advanced', models.BooleanField(default=False)),
                ('reduction_run', models.ForeignKey(related_name=b'run_variables', to='reduction_viewer.ReductionRun')),
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
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='runvariable',
            name='scripts',
            field=models.ManyToManyField(to='reduction_variables.ScriptFile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrumentvariable',
            name='scripts',
            field=models.ManyToManyField(to='reduction_variables.ScriptFile'),
            preserve_default=True,
        ),
    ]
