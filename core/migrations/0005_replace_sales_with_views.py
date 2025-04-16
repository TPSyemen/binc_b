from django.db import migrations, models


def remove_sales_field(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    if 'sales' in [field.name for field in Product._meta.get_fields()]:
        schema_editor.execute("ALTER TABLE core_product DROP COLUMN sales")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_product_in_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='views',
            field=models.PositiveIntegerField(default=0, verbose_name='Views', help_text='Number of times the product has been viewed.'),
        ),
        migrations.RunPython(remove_sales_field, reverse_code=migrations.RunPython.noop),
    ]
