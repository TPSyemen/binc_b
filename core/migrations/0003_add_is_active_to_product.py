from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_category_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(
                default=True,
                verbose_name='Is Active',
                help_text='Indicates whether the product is active and visible.'
            ),
        ),
    ]
