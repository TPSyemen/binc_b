from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_add_seller_rating'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Notification Content')),
                ('notification_type', models.CharField(choices=[('promotion', 'Promotion'), ('order', 'Order Update'), ('general', 'General')], default='general', max_length=20)),
                ('is_read', models.BooleanField(default=False, verbose_name='Is Read')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.user')),
            ],
        ),
    ]
