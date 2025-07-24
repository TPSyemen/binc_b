"""
comparison/admin.py
------------------
Admin configuration for comparison models.
"""

"""
comparison/admin.py
-------------------
Admin interface for comparison models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ProductComparison, ComparisonCriteria, ComparisonResult,
    ComparisonTemplate, ComparisonShare, TemplateCriteria
)


@admin.register(ComparisonCriteria)
class ComparisonCriteriaAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'criteria_type', 'weight', 'is_higher_better', 'is_active'
    ]
    list_filter = ['criteria_type', 'is_higher_better', 'is_active']
    search_fields = ['name']
    ordering = ['criteria_type', 'name']


class TemplateCriteriaInline(admin.TabularInline):
    model = TemplateCriteria
    extra = 1
    fields = ['criteria', 'custom_weight']


@admin.register(ComparisonTemplate)
class ComparisonTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'is_default', 'usage_count', 'created_at'
    ]
    list_filter = ['category', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at']
    inlines = [TemplateCriteriaInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'is_default')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProductComparison)
class ProductComparisonAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'products_count', 'is_public', 'created_at'
    ]
    list_filter = ['is_public', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['products']

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = [
        'comparison', 'winner_product', 'calculated_at'
    ]
    list_filter = ['calculated_at']
    search_fields = ['comparison__name', 'winner_product__name']
    readonly_fields = ['calculated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('comparison', 'winner_product', 'calculated_at')
        }),
        ('Detailed Results', {
            'fields': ('overall_scores', 'criteria_breakdown', 'best_deals'),
            'classes': ('collapse',)
        })
    )


@admin.register(ComparisonShare)
class ComparisonShareAdmin(admin.ModelAdmin):
    list_display = [
        'comparison', 'share_token', 'view_count', 'expires_at', 'created_at'
    ]
    list_filter = ['expires_at', 'created_at']
    search_fields = ['comparison__name', 'share_token']
    readonly_fields = ['share_token', 'view_count', 'created_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['comparison']
        return self.readonly_fields
