from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        SOFT = "Soft"
        HARD = "Hard"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=63, choices=CoverChoices.choices)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title}, author-{self.author}"

    class Meta:
        ordering = ["title"]
