import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class CaptchaGenerator:
    @staticmethod
    def generate_math_captcha():
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        answer = a + b
        question = f"Решите: {a} + {b} = ?"
        return question, str(answer)

    @staticmethod
    def get_captcha_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Я человек!", callback_data="human_verification")]
        ])