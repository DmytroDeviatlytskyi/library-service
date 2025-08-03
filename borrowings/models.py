from django.db import models

from books.models import Book
from library_service import settings


class Borrowing(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return (
            f"{self.user.first_name} {self.user.last_name} "
            f"email: {self.user.email} borrowed {self.book}"
        )
