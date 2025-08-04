from django.db import transaction, IntegrityError
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


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")

    def validate(self, data):
        book = data["book"]
        if book.inventory < 1:
            raise serializers.ValidationError(
                {"detail": f"Book `{book.title}` does not have in inventory"}
            )
        return data

    def create(self, validated_data):
        book = validated_data.pop("book")
        try:
            with transaction.atomic():
                book.inventory -= 1
                book.save()
                borrowing = Borrowing.objects.create(
                    book=book,
                    **validated_data,
                )
                return borrowing
        except IntegrityError:
            raise serializers.ValidationError(
                {"detail": f"User has already borrowed book `{book.title}`"}
            )
