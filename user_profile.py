import json
from typing import Dict, Optional
from pathlib import Path
import random
import string
import time
import os
import datetime

class UserProfile:
    def __init__(self, user_id: str):  
        self.user_id = user_id
        self.data = {
            'settings': {
                'language': None,
                'model': 'gpt-4'
            },
            'messages_count': 0,
            'history': [],
            'registration_key': f'MLA-{user_id}',
            'is_registered': False
        }
        self.profiles_dir = Path('profiles')
        self.profiles_dir.mkdir(exist_ok=True)
        self.profile_path = self.profiles_dir / f'{user_id}.json'
        self.load_profile()

    def generate_registration_key(self) -> str:
        """Генерация уникального ключа регистрации"""
        timestamp = str(int(time.time()))
        random_digits = ''.join(random.choices(string.digits, k=6))
        key = f"moon-{timestamp}-{random_digits}"
        self.data['registration_key'] = key
        self.save_profile()
        return key

    def get_registration_key(self) -> str:
        """Получение ключа регистрации"""
        return self.data.get('registration_key')

    def load_profile(self) -> None:
        """Загрузка профиля пользователя из файла"""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    if 'settings' not in saved_data:
                        saved_data['settings'] = {}
                    if 'is_registered' not in saved_data:
                        saved_data['is_registered'] = False
                    if 'registration_key' not in saved_data:
                        saved_data['registration_key'] = None
                    if 'language' not in saved_data['settings']:
                        saved_data['settings']['language'] = None
                    if 'model' not in saved_data['settings']:
                        saved_data['settings']['model'] = 'gpt-4'
                    if 'history' not in saved_data:
                        saved_data['history'] = []
                    
                    # Проверяем, что модель из списка доступных
                    from bot import AVAILABLE_MODELS
                    if saved_data['settings'].get('model') not in AVAILABLE_MODELS:
                        saved_data['settings']['model'] = 'gpt-4'
                    
                    self.data.update(saved_data)
            except Exception as e:
                print(f"Error loading profile: {e}")

    def save_profile(self) -> None:
        """Сохранение профиля пользователя в файл"""
        try:
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving profile: {e}")

    def increment_messages(self) -> None:
        """Увеличение счетчика сообщений"""
        self.data['messages_count'] += 1
        self.save_profile()

    def set_favorite_model(self, model: str) -> None:
        """Установка предпочитаемой модели"""
        self.data['settings']['model'] = model  
        self.save_profile()

    def update_settings(self, settings: Dict) -> None:
        """Обновление настроек пользователя"""
        if 'settings' not in self.data:
            self.data['settings'] = {}
        self.data['settings'].update(settings)
        self.save_profile()

    def is_registered(self):
        """Проверяет, установлен ли язык в профиле"""
        return self.data['settings']['language'] is not None

    def get_language(self):
        """Возвращает текущий язык или 'ru' если язык не установлен"""
        return self.data['settings'].get('language', 'ru')

    def set_language(self, language):
        """Устанавливает язык в профиле"""
        self.data['settings']['language'] = language
        self.save_profile()

    def complete_registration(self, language: str) -> None:
        """Завершение регистрации пользователя"""
        self.data['is_registered'] = True
        self.data['settings']['language'] = language
        self.save_profile()

    def get_stats(self) -> str:
        """Получение статистики пользователя"""
        return (
            f"📊 Статистика профиля:\n"
            f"└ ID: {self.user_id}\n"
            f"└ Ключ: {self.data.get('registration_key', 'Не назначен')}\n"
            f"└ Отправлено сообщений: {self.data['messages_count']}\n"
            f"└ Модель: {self.data['settings'].get('model', 'не выбрана')}\n"
            f"└ Язык: {self.data['settings'].get('language', 'ru')}"
        )

    def add_to_history(self, message, response):
        """Добавляет сообщение и ответ в историю"""
        self.data['history'].append({
            'message': message,
            'response': response,
            'timestamp': str(datetime.datetime.now()),
            'model': self.data['settings'].get('model', 'gpt-4')
        })
        # Ограничиваем историю последними 10 сообщениями
        if len(self.data['history']) > 10:
            self.data['history'] = self.data['history'][-10:]
        self.save_profile()

    def get_history(self):
        """Возвращает историю сообщений"""
        return self.data.get('history', [])

class ProfileManager:
    _instances = {}

    @classmethod
    def get_profile(cls, user_id: str) -> UserProfile:  
        """Получение профиля пользователя (синглтон)"""
        if user_id not in cls._instances:
            cls._instances[user_id] = UserProfile(user_id)
        return cls._instances[user_id]
