from django.core.management.base import BaseCommand
from core.models import Product, Category, Shop, Owner, User
from decimal import Decimal
import uuid

class Command(BaseCommand):
    help = 'Adds sample products to the database'

    def handle(self, *args, **options):
        # Verificar si ya existen productos
        if Product.objects.count() > 0:
            self.stdout.write(self.style.WARNING('Ya existen productos en la base de datos. No se añadirán productos de muestra.'))
            return

        # Verificar si existe al menos un propietario con tienda
        try:
            owner = Owner.objects.filter(shop__isnull=False).first()
            if not owner:
                self.stdout.write(self.style.ERROR('No se encontró ningún propietario con tienda. Por favor, crea un propietario y una tienda primero.'))
                return
            
            shop = owner.shop
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al buscar propietarios: {e}'))
            return

        # Crear categorías si no existen
        categories = {
            'electronics': 'Electrónica',
            'clothing': 'Ropa',
            'home': 'Hogar',
            'books': 'Libros',
            'sports': 'Deportes'
        }
        
        category_objects = {}
        for key, name in categories.items():
            category, created = Category.objects.get_or_create(name=name)
            category_objects[key] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoría creada: {name}'))

        # Crear productos de muestra
        sample_products = [
            {
                'name': 'Smartphone Premium',
                'description': 'Un smartphone de alta gama con las últimas características y tecnología.',
                'price': Decimal('999.99'),
                'original_price': Decimal('1299.99'),
                'category': category_objects['electronics'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 15,
                'is_active': True
            },
            {
                'name': 'Laptop Profesional',
                'description': 'Laptop potente para profesionales y gamers con procesador de última generación.',
                'price': Decimal('1499.99'),
                'original_price': Decimal('1799.99'),
                'category': category_objects['electronics'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 8,
                'is_active': True
            },
            {
                'name': 'Auriculares Inalámbricos',
                'description': 'Auriculares con cancelación de ruido y calidad de sonido excepcional.',
                'price': Decimal('199.99'),
                'original_price': Decimal('249.99'),
                'category': category_objects['electronics'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 25,
                'is_active': True
            },
            {
                'name': 'Camiseta Premium',
                'description': 'Camiseta de algodón de alta calidad con diseño exclusivo.',
                'price': Decimal('29.99'),
                'original_price': Decimal('39.99'),
                'category': category_objects['clothing'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 50,
                'is_active': True
            },
            {
                'name': 'Zapatillas Deportivas',
                'description': 'Zapatillas cómodas y duraderas para todo tipo de actividades.',
                'price': Decimal('89.99'),
                'original_price': Decimal('119.99'),
                'category': category_objects['sports'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 30,
                'is_active': True
            },
            {
                'name': 'Lámpara de Mesa',
                'description': 'Lámpara elegante y funcional para tu hogar u oficina.',
                'price': Decimal('49.99'),
                'original_price': Decimal('69.99'),
                'category': category_objects['home'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 20,
                'is_active': True
            },
            {
                'name': 'Libro de Programación',
                'description': 'Guía completa para aprender programación desde cero.',
                'price': Decimal('34.99'),
                'original_price': Decimal('44.99'),
                'category': category_objects['books'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 40,
                'is_active': True
            },
            {
                'name': 'Reloj Inteligente',
                'description': 'Reloj con múltiples funciones para monitorear tu salud y actividades.',
                'price': Decimal('149.99'),
                'original_price': Decimal('199.99'),
                'category': category_objects['electronics'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 12,
                'is_active': True
            },
            {
                'name': 'Mochila Resistente',
                'description': 'Mochila espaciosa y duradera para tus aventuras diarias.',
                'price': Decimal('59.99'),
                'original_price': Decimal('79.99'),
                'category': category_objects['clothing'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 35,
                'is_active': True
            },
            {
                'name': 'Set de Cocina',
                'description': 'Conjunto completo de utensilios de cocina de alta calidad.',
                'price': Decimal('129.99'),
                'original_price': Decimal('169.99'),
                'category': category_objects['home'],
                'image_url': 'https://via.placeholder.com/300',
                'stock': 15,
                'is_active': True
            }
        ]

        # Añadir productos a la base de datos
        for product_data in sample_products:
            product = Product(
                id=uuid.uuid4(),
                shop=shop,
                **product_data
            )
            product.save()
            self.stdout.write(self.style.SUCCESS(f'Producto creado: {product.name}'))

        self.stdout.write(self.style.SUCCESS(f'Se han añadido {len(sample_products)} productos de muestra a la tienda de {owner.user.username}'))
