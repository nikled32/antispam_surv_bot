import json
import time
from pathlib import Path

class PendingUsersStorage:
    def __init__(self):
        self.file_path = Path("data/pending_users.json")
        self._ensure_storage()

    def _ensure_storage(self):
        """Создает файл хранилища при необходимости"""
        self.file_path.parent.mkdir(exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding='utf-8')

    def _load_data(self) -> dict:
        """Загружает данные из JSON-файла"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: dict):
        """Сохраняет данные в JSON-файл"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_user(self, user_id: str, chat_id: str, question: str, answer: str):
        """Добавляет нового пользователя в хранилище"""
        data = self._load_data()
        data[user_id] = {
            "chat_id": chat_id,
            "question": question,
            "answer": answer,
            "timestamp": int(time.time())
        }
        self._save_data(data)

    def get_user_data(self, user_id: str) -> dict:
        """Получает данные пользователя"""
        return self._load_data().get(user_id, {})

    def remove_user(self, user_id: str):
        """Удаляет пользователя из хранилища"""
        data = self._load_data()
        if user_id in data:
            del data[user_id]
            self._save_data(data)