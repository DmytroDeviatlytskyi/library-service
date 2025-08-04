from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = ("id", "user", "book", "borrow_date", "expected_return_date")
