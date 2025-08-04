from rest_framework import generics

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingDetailSerializer,
    BorrowingListSerializer,
)


class BorrowingListView(generics.ListAPIView):
    queryset = Borrowing.objects.select_related("user", "book")
    serializer_class = BorrowingListSerializer


class BorrowingDetailView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.select_related("user", "book")
    serializer_class = BorrowingDetailSerializer
