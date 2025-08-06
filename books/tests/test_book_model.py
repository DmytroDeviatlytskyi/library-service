from django.test import TestCase

from books.models import Book


class BookModelTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Book 1",
            author="Test Author",
            cover="Soft",
            inventory=5,
            daily_fee=0.45,
        )

    def test_create_book(self):
        book_2 = Book.objects.create(
            title="Book 2",
            author="Test Author",
            cover="Hard",
            inventory=2,
            daily_fee=0.99,
        )
        books = Book.objects.all()

        self.assertEqual(books.count(), 2)
        self.assertIn(self.book, books)
        self.assertIn(book_2, books)

    def test_str_book(self):
        self.assertEqual(
            str(self.book), f"{self.book.title}, author: {self.book.author}"
        )
