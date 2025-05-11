from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def enable_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
