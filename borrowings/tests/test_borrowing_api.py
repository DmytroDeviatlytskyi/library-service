from datetime import timedelta
from unittest.mock import patch, AsyncMock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

import borrowings
from books.tests.test_book_api import create_book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)

BORROWING_URL = reverse("borrowings:borrowings-list")


def borrowing_detail_url(borrowing_id):
    return reverse("borrowings:borrowings-detail", args=[borrowing_id])


def create_borrowing(**kwargs):
    book = create_book()
    payload = {
        "book": book,
        "expected_return_date": now().date() + timedelta(days=10),
    }
    payload.update(**kwargs)
    return Borrowing.objects.create(**payload)


class PublicBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_borrowing_list_auth_required(self):
        response = self.client.get(BORROWING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_borrowing_detail_auth_required(self):
        response = self.client.get(borrowing_detail_url(1))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_borrowing_list(self, mock_send_telegram_message):
        create_borrowing(user=self.user)
        response = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.filter(user=self.user)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_filter_borrowings_by_is_active(self, mock_send_telegram_message):
        borrowing_without_return_date = create_borrowing(user=self.user)
        new_book = create_book(title="Book Title 2")
        return_date = now().date() + timedelta(days=11)
        borrowing_with_return_date = create_borrowing(
            user=self.user, actual_return_date=return_date, book=new_book
        )
        response = self.client.get(BORROWING_URL, {"is_active": "true"})

        serializer_1 = BorrowingListSerializer(borrowing_without_return_date)
        serializer_2 = BorrowingListSerializer(borrowing_with_return_date)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, response.data["results"])
        self.assertNotIn(serializer_2.data, response.data["results"])

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_borrowing_detail(self, mock_send_telegram_message):
        borrowing = create_borrowing(user=self.user)
        url = borrowing_detail_url(borrowing.id)
        response = self.client.get(url)
        serializer = BorrowingDetailSerializer(borrowing)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_return_borrowing(self, mock_send_telegram_message):
        new_book = create_book(inventory=4)
        borrowing = create_borrowing(user=self.user, book=new_book)
        url = reverse(
            "borrowings:borrowings-return-borrowing", args=[borrowing.id]
        )
        return_date = now().date() + timedelta(days=10)
        response_1 = self.client.post(url, {"actual_return_date": return_date})
        borrowing.refresh_from_db()
        new_book.refresh_from_db()

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_1.data, {"message": "The book: `Test Book` was returned."}
        )
        self.assertEqual(new_book.inventory, 5)
        self.assertEqual(borrowing.actual_return_date, return_date)

        response_2 = self.client.post(url, {"actual_return_date": ""})
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_2.data, {"detail": "This book is already returned"}
        )

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_return_borrowing_without_actual_return_date(
        self, mock_send_telegram_message
    ):
        borrowing = create_borrowing(user=self.user)
        url = reverse(
            "borrowings:borrowings-return-borrowing", args=[borrowing.id]
        )
        response_1 = self.client.post(url, {"actual_return_date": ""})
        borrowing.refresh_from_db()
        return_date = now().date()

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_1.data, {"message": "The book: `Test Book` was returned."}
        )
        self.assertEqual(borrowing.actual_return_date, return_date)

    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def test_create_borrowing(self, mock_send_telegram_message):
        book = create_book(title="Test Title")
        payload = {
            "book": book.id,
            "user": self.user.id,
            "expected_return_date": now().date() + timedelta(days=10),
        }
        response = self.client.post(BORROWING_URL, payload)
        borrowing = Borrowing.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(getattr(borrowing, "book"), book)
        self.assertEqual(getattr(borrowing, "user"), self.user)
        self.assertEqual(
            getattr(borrowing, "expected_return_date"),
            payload["expected_return_date"],
        )


class AdminBorrowingApiTests(TestCase):
    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def setUp(self, mock_send_telegram_message):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)
        self.borrowing = create_borrowing(user=self.user)
        self.test_user = get_user_model().objects.create_user(
            email="user@test.com", password="user_password"
        )
        create_borrowing(user=self.test_user)

    def test_borrowing_list(self):
        response = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_borrowing_list_by_user_id(self):
        response = self.client.get(BORROWING_URL, {"user_id": self.user.id})
        borrowings_with_correct_user = Borrowing.objects.filter(user=self.user)
        borrowings_with_incorrect_user = Borrowing.objects.filter(
            user=self.test_user
        )

        serializer_1 = BorrowingListSerializer(
            borrowings_with_correct_user, many=True
        )
        serializer_2 = BorrowingListSerializer(
            borrowings_with_incorrect_user, many=True
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data[0], response.data["results"])
        self.assertNotIn(serializer_2.data[0], response.data["results"])
