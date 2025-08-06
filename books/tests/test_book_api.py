from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from books.models import Book
from books.serializers import BookListSerializer, BookSerializer

BOOK_URL = reverse("books:books-list")


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


def book_detail_url(book_id):
    return reverse("books:books-detail", args=[book_id])


class PublicBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = create_book()

    def test_book_list(self):
        create_book(title="Test Book 2")
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data["results"])


class PrivateBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test-password"
        )
        self.client.force_authenticate(self.user)
        self.book = create_book()

    def test_book_list(self):
        create_book(title="Test Book 2")
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data["results"])

    def test_book_detail(self):
        response = self.client.get(book_detail_url(self.book.id))
        serializer = BookSerializer(self.book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data)

    def test_create_book_forbidden(self):
        payload = {
            "title": "Test Book 2",
            "author": "Test Author",
            "cover": "Hard",
            "inventory": 2,
            "daily_fee": 0.25,
        }
        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_book_forbidden(self):
        payload = {
            "title": "Test Book 2",
            "author": "Test Author",
        }
        url = book_detail_url(self.book.id)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_book_forbidden(self):
        payload = {
            "title": "New Title",
            "author": "New Author",
            "cover": "Hard",
            "inventory": 10,
            "daily_fee": 10.99,
        }
        url = book_detail_url(self.book.id)
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_book_forbidden(self):
        url = book_detail_url(self.book.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test-password"
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = {
            "title": "Book",
            "author": "Author",
            "cover": "Soft",
            "inventory": 3,
            "daily_fee": 0.50,
        }
        response = self.client.post(BOOK_URL, payload)
        book = Book.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["title"], getattr(book, "title"))
        self.assertEqual(payload["author"], getattr(book, "author"))
        self.assertEqual(payload["cover"], getattr(book, "cover"))
        self.assertEqual(payload["inventory"], getattr(book, "inventory"))
        self.assertEqual(payload["daily_fee"], getattr(book, "daily_fee"))

    def test_patch_book(self):
        book = create_book()
        payload = {
            "title": "New Book",
        }
        url = book_detail_url(book.id)
        response = self.client.patch(url, payload)
        book.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(book.title, payload["title"])

    def test_put_book(self):
        book = create_book()
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "Hard",
            "inventory": 1,
            "daily_fee": 0.15,
        }
        url = book_detail_url(book.id)
        response = self.client.put(url, payload)
        book.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(book.title, payload["title"])
        self.assertEqual(book.author, payload["author"])
        self.assertEqual(book.cover, payload["cover"])
        self.assertEqual(book.inventory, payload["inventory"])
        self.assertEqual(book.daily_fee, Decimal("0.15"))

    def test_delete_book(self):
        book = create_book()
        url = book_detail_url(book.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
