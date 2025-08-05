from django.db import transaction
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingDetailSerializer,
    BorrowingListSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("user", "book")
    serializer_class = BorrowingCreateSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Only staff users can filter borrowings by user_id.
        Non-admin users can see only their own borrowings.
        """
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = self.queryset.filter(user=self.request.user)

        is_active = self.request.query_params.get("is_active")
        if is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        elif self.action == "retrieve":
            return BorrowingDetailSerializer

        elif self.action == "return_borrowing":
            return BorrowingReturnSerializer

        return BorrowingCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        request=BorrowingReturnSerializer,
        description="Endpoint for return borrowing book",
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def return_borrowing(self, request, *args, **kwargs):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response(
                {"detail": "This book is already returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if request.data["actual_return_date"]:
                borrowing.actual_return_date = request.data[
                    "actual_return_date"
                ]
            else:
                borrowing.actual_return_date = now().date()
            borrowing.save()
            borrowing.book.inventory += 1
            borrowing.book.save()

            return Response(
                {
                    "message": f"The book:"
                    f" `{borrowing.book.title}` was returned."
                },
                status=status.HTTP_200_OK,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=str,
                description=(
                    "Filter borrowings by `is_active` if "
                    "actual_return_date is null (ex. `?is_active=true`)"
                ),
            ),
            OpenApiParameter(
                "user_id",
                type=str,
                description=(
                    "Filter borrowings by `user_id` "
                    "for admin-user (ex. `?user_id=3`)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of borrowings"""
        return super().list(request, *args, **kwargs)
