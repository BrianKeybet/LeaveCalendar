# Generated by Django 4.2.1 on 2023-06-20 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycalendar', '0003_leaverequest_leave_bal'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='leave_ent',
            field=models.IntegerField(default='0'),
        ),
    ]