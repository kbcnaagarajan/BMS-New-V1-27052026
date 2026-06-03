from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0004_company_currency_company_timezone_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backend', models.CharField(default='django.core.mail.backends.smtp.EmailBackend', max_length=255)),
                ('host', models.CharField(default='smtp.gmail.com', max_length=255)),
                ('port', models.IntegerField(default=587)),
                ('host_user', models.CharField(blank=True, max_length=255)),
                ('host_password', models.CharField(blank=True, max_length=255)),
                ('use_tls', models.BooleanField(default=True)),
                ('use_ssl', models.BooleanField(default=False)),
                ('default_from_email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_settings', to='user_management.company')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='user_management.user')),
            ],
            options={
                'verbose_name_plural': 'Email Settings',
            },
        ),
    ]
