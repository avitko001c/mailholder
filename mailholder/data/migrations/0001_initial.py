# Generated by Django 2.2.5 on 2019-12-01 21:08

import data.fields
import data.models
import data.utils
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emailaddress', models.EmailField(max_length=255)),
                ('from_email', models.CharField(max_length=254, validators=[data.utils.validate_email_with_name], verbose_name='Email From')),
                ('to', data.fields.CommaSeparatedEmailField(blank=True, verbose_name='Email To')),
                ('cc', data.fields.CommaSeparatedEmailField(blank=True, verbose_name='Cc')),
                ('bcc', data.fields.CommaSeparatedEmailField(blank=True, verbose_name='Bcc')),
                ('subject', models.CharField(blank=True, max_length=989, verbose_name='Subject')),
                ('message', models.TextField(blank=True, verbose_name='Message')),
                ('html_message', models.TextField(blank=True, verbose_name='HTML Message')),
                ('status', models.PositiveSmallIntegerField(blank=True, choices=[(0, 'sent'), (1, 'failed'), (2, 'queued')], db_index=True, null=True, verbose_name='Status')),
                ('priority', models.PositiveSmallIntegerField(blank=True, choices=[(0, 'low'), (1, 'medium'), (2, 'high'), (3, 'now')], null=True, verbose_name='Priority')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('scheduled_time', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='The scheduled sending time')),
                ('headers', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='Headers')),
                ('context', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='Context')),
                ('backend_alias', models.CharField(blank=True, default='', max_length=64, verbose_name='Backend alias')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('email_address', models.EmailField(max_length=255, verbose_name='Email')),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'sent'), (1, 'failed')], verbose_name='Status')),
                ('exception_type', models.CharField(blank=True, max_length=255, verbose_name='Exception type')),
                ('message', models.TextField(verbose_name='Message')),
                ('email', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='data.Email', verbose_name='Email address')),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="e.g: 'welcome_email'", max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, help_text='Description of this template.', verbose_name='Description')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('subject', models.CharField(blank=True, max_length=255, validators=[data.utils.validate_template_syntax], verbose_name='Subject')),
                ('content', models.TextField(blank=True, validators=[data.utils.validate_template_syntax], verbose_name='Content')),
                ('html_content', models.TextField(blank=True, validators=[data.utils.validate_template_syntax], verbose_name='HTML content')),
                ('language', models.CharField(blank=True, default='', help_text='Render template in alternative language', max_length=12, verbose_name='Language')),
                ('default_template', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translated_templates', to='data.EmailTemplate', verbose_name='Default template')),
            ],
        ),
        migrations.AddField(
            model_name='email',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='data.EmailTemplate', verbose_name='Email template'),
        ),
        migrations.AddField(
            model_name='email',
            name='username',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='data.User', verbose_name='User Name'),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=data.models.get_upload_path, verbose_name='File')),
                ('filename', models.CharField(help_text='The original filename', max_length=255, verbose_name='Filename')),
                ('mimetype', models.CharField(blank=True, default='', max_length=255)),
                ('headers', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='Headers')),
                ('emails', models.ManyToManyField(related_name='attachments', to='data.Email', verbose_name='Email addresses')),
            ],
        ),
    ]