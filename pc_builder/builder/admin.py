from django.contrib import admin

from .models import Category, Component, SavedBuild


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "name_pl", "sort_order")


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price_pln", "power_watts")
    list_filter = ("category",)
    search_fields = ("name", "description")


@admin.register(SavedBuild)
class SavedBuildAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "total_price_pln", "updated_at")
    search_fields = ("title", "user__username")
