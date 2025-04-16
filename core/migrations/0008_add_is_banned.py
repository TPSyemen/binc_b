from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_user_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_banned',
            field=models.BooleanField(
                default=False,
                verbose_name='Is Banned',
                help_text='Indicates whether the user is banned.'
            ),
        ),
        migrations.AddField(
            model_name='shop',
            name='is_banned',
            field=models.BooleanField(
                default=False,
                verbose_name='Is Banned',
                help_text='Indicates whether the shop is banned.'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='is_banned',
            field=models.BooleanField(
                default=False,
                verbose_name='Is Banned',
                help_text='Indicates whether the product is banned.'
            ),
        ),
    ]
