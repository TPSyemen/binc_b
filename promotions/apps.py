"""
promotions/apps.py
------------------
AppConfig for the promotions app.
"""

from django.apps import AppConfig


class PromotionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'promotions'
