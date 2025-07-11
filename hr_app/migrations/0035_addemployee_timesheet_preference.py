# Generated by Django 5.1.7 on 2025-06-23 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr_app', '0034_exitrequest_email_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='addemployee',
            name='timesheet_preference',
            field=models.CharField(choices=[('daily', 'Daily Timesheet'), ('weekly', 'Weekly Timesheet'), ('image', 'Image Timesheet')], default='daily', help_text="The user's preferred method for filling out their timesheet.", max_length=10),
        ),
    ]
