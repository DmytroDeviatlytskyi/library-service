from datetime import timedelta
from unittest.mock import patch, AsyncMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from books.models import Book
from borrowings.models import Borrowing


def create_book(**kwargs):
    payload = {
        "title": "Test Book",
        "author": "Test Author",
        "cover": "Soft",
        "inventory": 5,
        "daily_fee": 0.99,
    }
    payload.update(**kwargs)
    return Book.objects.create(**payload)


class BorrowingModelTests(TestCase):

    @classmethod
    @patch("borrowings.signals.send_telegram_message", new_callable=AsyncMock)
    def setUpTestData(cls, mock_send_telegram_message):
        cls.book = create_book()
        cls.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="test_password",
        )
        cls.borrowing = Borrowing.objects.create(
            user = cls.user,
            book = cls.book,
            expected_return_date = now().date() + timedelta(days=10)
        )

    def test_create_borrowing(self, ):
        borrowings = Borrowing.objects.all()
        self.assertEqual(borrowings.count(), 1)
        self.assertIn(self.borrowing, borrowings)

    def test_borrowing_str(self):
        self.assertEqual(str(self.borrowing), f"{self.user} email: {self.user.email} borrowed {self.book}")
