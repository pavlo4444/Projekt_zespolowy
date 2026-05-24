from django.db import models


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name_pl = models.CharField("Nazwa (PL)", max_length=120)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "slug"]
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self) -> str:
        return self.name_pl


class Component(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="components")
    name = models.CharField(max_length=220)
    description = models.TextField("Opis / funkcje", blank=True)
    price_pln = models.DecimalField("Cena (PLN)", max_digits=10, decimal_places=2)
    power_watts = models.PositiveIntegerField("Pobór mocy (W)", default=0, help_text="Dla zasilacza: moc nominalna (W).")
    specs = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Komponent"
        verbose_name_plural = "Komponenty"

    def __str__(self) -> str:
        return f"{self.name} ({self.category.slug})"


class SavedBuild(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="saved_builds")
    title = models.CharField(max_length=160, default="Mój zestaw")
    components = models.JSONField(default=dict, help_text="Mapa slug_kategorii -> id komponentu")
    total_price_pln = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_power_w = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Zapisany zestaw"
        verbose_name_plural = "Zapisane zestawy"

    def __str__(self) -> str:
        return f"{self.title} ({self.user})"
