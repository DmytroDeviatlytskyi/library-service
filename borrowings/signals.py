import asyncio
import os

import telegram
from django.db.models.signals import post_save
from django.dispatch import receiver
from dotenv import load_dotenv

from borrowings.models import Borrowing

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=TOKEN)


@receiver(post_save, sender=Borrowing)
def notify_new_borrowing(sender, instance, created, **kwargs):
    if created:
        message = (
            f"New borrowing:\n "
            f"User: {instance.user} \n "
            f"Book: {instance.book}\n "
            f"Expected return date: {instance.expected_return_date}\n "
            f"Borrow date: {instance.borrow_date}"
        )
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
