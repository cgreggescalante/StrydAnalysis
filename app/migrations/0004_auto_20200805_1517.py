# Generated by Django 3.1 on 2020-08-05 20:17
from datetime import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20200804_1833'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='bounding_box',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='start_position',
        ),
        migrations.RemoveField(
            model_name='lap',
            name='bounding_box',
        ),
        migrations.RemoveField(
            model_name='lap',
            name='end_position',
        ),
        migrations.RemoveField(
            model_name='lap',
            name='start_position',
        ),
        migrations.RemoveField(
            model_name='record',
            name='position',
        ),
        migrations.AddField(
            model_name='activity',
            name='start_position_lat',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activity',
            name='start_position_long',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lap',
            name='end_position_lat',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lap',
            name='end_position_long',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lap',
            name='end_time',
            field=models.DateTimeField(default=datetime(1, 1, 1)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lap',
            name='start_position_lat',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lap',
            name='start_position_long',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='record',
            name='position_lat',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='record',
            name='position_long',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
