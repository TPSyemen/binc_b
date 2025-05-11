from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProductReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction_type', models.CharField(choices=[('like', 'Like'), ('dislike', 'Dislike'), ('neutral', 'Neutral')], default='neutral', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_reactions', to='core.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_reactions', to='core.user')),
            ],
            options={
                'verbose_name': 'User Product Reaction',
                'verbose_name_plural': 'User Product Reactions',
                'unique_together': {('user', 'product')},
            },
        ),
    ]
