from django.urls import path
from .views_categories import (
    CategoryListView, CategoryDetailView, CategoryCreateView,
    CategoryUpdateView, CategoryDeleteView
)

urlpatterns = [
    path('', CategoryListView.as_view(), name='category-list'),
    path('<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('create/', CategoryCreateView.as_view(), name='category-create'),
    path('<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
]
