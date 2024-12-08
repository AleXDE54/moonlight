import json
import telebot
from telebot import types
import g4f
import requests
import datetime

from config import token, serverprompt
from user_profile import ProfileManager
from translations import get_text, LANGUAGE_NAMES

AVAILABLE_MODELS = [
    'mixtral-8x7b',
    'gemini-pro',
    'gpt-4'
]

MODEL_DISPLAY_NAMES = {
    'mixtral-8x7b': 'moonlight-pro',
    'gemini-pro': 'moonlight',
    'gpt-4': 'gpt-4'
}

bot = telebot.TeleBot(token)

def translate_text(text, target_lang='ru'):
    try:
        # Используем Google Translate API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params)
        translation = response.json()[0][0][0]
        return translation
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def get_ai_response(message, profile, model_name='gpt-4', language='ru'):
    try:
        # Получаем всю историю сообщений пользователя
        history = profile.data.get('history', [])
        
        # Формируем список сообщений с учетом истории
        messages = [{"role": "system", "content": serverprompt}]
        
        # Добавляем все сообщения из истории
        for hist_item in history:
            messages.append({"role": "user", "content": hist_item['message']})
            messages.append({"role": "assistant", "content": hist_item['response']})
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": message})
        
        # Ограничиваем количество токенов, чтобы не превысить лимит модели
        max_tokens = 4000  # Примерное ограничение для большинства моделей
        total_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        # Если превышаем лимит, урезаем историю
        while total_tokens > max_tokens and len(messages) > 2:
            messages.pop(1)  # Удаляем старые сообщения, оставляя системный промпт
            total_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        response = g4f.ChatCompletion.create(
            model=model_name,
            messages=messages,
            stream=False,
        )
        answer = response
        
        if language != 'en':
            answer = translate_text(answer, language)
        
        return answer
    except Exception as e:
        return f"Ошибка генерации ответа: {e}"

def create_main_menu(lang_code):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_select_model'), callback_data='show_models'),
        types.InlineKeyboardButton(get_text(lang_code, 'btn_profile'), callback_data='show_profile')
    )
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_language'), callback_data='show_languages')
    )
    return keyboard

def create_models_menu(lang_code):
    keyboard = types.InlineKeyboardMarkup()
    for model_name in AVAILABLE_MODELS:
        keyboard.row(
            types.InlineKeyboardButton(
                MODEL_DISPLAY_NAMES[model_name], 
                callback_data=f'select_model_{model_name}'
            )
        )
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_back'), callback_data='main_menu')
    )
    return keyboard

def create_languages_menu(lang_code):
    keyboard = types.InlineKeyboardMarkup()
    languages = ['ru', 'en', 'es', 'de', 'fr']
    for lang in languages:
        keyboard.row(
            types.InlineKeyboardButton(
                f"{LANGUAGE_NAMES[lang]} {LANGUAGE_NAMES[lang][0]}", 
                callback_data=f'select_language_{lang}'
            )
        )
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_back'), callback_data='main_menu')
    )
    return keyboard

def create_modify_response_menu(lang_code):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_shorter'), callback_data='modify_shorter'),
        types.InlineKeyboardButton(get_text(lang_code, 'btn_longer'), callback_data='modify_longer')
    )
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_simpler'), callback_data='modify_simpler'),
        types.InlineKeyboardButton(get_text(lang_code, 'btn_complex'), callback_data='modify_complex')
    )
    keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_back'), callback_data='main_menu')
    )
    return keyboard

def handle_start(message):
    profile = ProfileManager(message.from_user.id)
    
    if not profile.data.get('settings', {}).get('language'):
        bot.send_message(
            message.chat.id, 
            get_text('ru', 'select_language'), 
            reply_markup=create_languages_menu('ru')
        )
        return

    lang_code = profile.data['settings'].get('language', 'ru')
    welcome_text = (
        f"{get_text(lang_code, 'welcome')}\n\n"
        f"{get_text(lang_code, 'registration_key').format(profile.get_registration_key())}\n"
        f"{get_text(lang_code, 'current_model').format(MODEL_DISPLAY_NAMES[profile.data['settings'].get('model', 'gpt-4')])}\n"
        f"{get_text(lang_code, 'current_language').format(LANGUAGE_NAMES[lang_code])}\n\n"
        f"{get_text(lang_code, 'menu_hint')}"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=create_main_menu(lang_code)
    )

def handle_message(message):
    profile = ProfileManager(message.from_user.id)
    lang_code = profile.data['settings'].get('language', 'ru')
    
    if not profile.data.get('settings', {}).get('language'):
        bot.send_message(
            message.chat.id, 
            get_text('ru', 'select_language'), 
            reply_markup=create_languages_menu('ru')
        )
        return

    profile.data['last_message'] = message.text
    
    answer = get_ai_response(
        message.text, 
        profile, 
        profile.data['settings'].get('model', 'gpt-4'), 
        lang_code
    )
    
    profile.add_to_history(message.text, answer)
    
    response_keyboard = types.InlineKeyboardMarkup()
    response_keyboard.row(
        types.InlineKeyboardButton(get_text(lang_code, 'btn_regenerate'), callback_data='regenerate_response'),
        types.InlineKeyboardButton(get_text(lang_code, 'btn_modify'), callback_data='modify_response')
    )
    
    bot.send_message(
        message.chat.id, 
        answer, 
        reply_markup=response_keyboard
    )

def handle_callback(call):
    profile = ProfileManager(call.from_user.id)
    lang_code = profile.data['settings'].get('language', 'ru')

    if call.data == 'main_menu':
        bot.edit_message_text(
            get_text(lang_code, 'menu_hint'), 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu(lang_code)
        )
    elif call.data == 'show_models':
        bot.edit_message_text(
            get_text(lang_code, 'select_model'), 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_models_menu(lang_code)
        )
    elif call.data.startswith('select_model_'):
        model_name = call.data.split('_')[-1]
        profile.data['settings']['model'] = model_name
        profile.save()
        
        bot.answer_callback_query(call.id, get_text(lang_code, 'model_changed').format(MODEL_DISPLAY_NAMES[model_name]))
        
        welcome_text = (
            f"{get_text(lang_code, 'welcome')}\n\n"
            f"{get_text(lang_code, 'registration_key').format(profile.get_registration_key())}\n"
            f"{get_text(lang_code, 'current_model').format(MODEL_DISPLAY_NAMES[profile.data['settings'].get('model', 'gpt-4')])}\n"
            f"{get_text(lang_code, 'current_language').format(LANGUAGE_NAMES[lang_code])}\n\n"
            f"{get_text(lang_code, 'menu_hint')}"
        )
        
        bot.edit_message_text(
            welcome_text, 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu(lang_code)
        )
    elif call.data == 'show_languages':
        bot.edit_message_text(
            get_text(lang_code, 'select_language'), 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_languages_menu(lang_code)
        )
    elif call.data.startswith('select_language_'):
        new_lang = call.data.split('_')[-1]
        profile.data['settings']['language'] = new_lang
        profile.save()
        
        bot.answer_callback_query(call.id, get_text(new_lang, 'language_changed').format(LANGUAGE_NAMES[new_lang]))
        
        welcome_text = (
            f"{get_text(new_lang, 'welcome')}\n\n"
            f"{get_text(new_lang, 'registration_key').format(profile.get_registration_key())}\n"
            f"{get_text(new_lang, 'current_model').format(MODEL_DISPLAY_NAMES[profile.data['settings'].get('model', 'gpt-4')])}\n"
            f"{get_text(new_lang, 'current_language').format(LANGUAGE_NAMES[new_lang])}\n\n"
            f"{get_text(new_lang, 'menu_hint')}"
        )
        
        bot.edit_message_text(
            welcome_text, 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu(new_lang)
        )
    elif call.data == 'show_profile':
        profile_stats = get_text(lang_code, 'profile_stats').format(
            profile.data['id'],
            profile.get_registration_key(),
            len(profile.data.get('history', [])),
            MODEL_DISPLAY_NAMES[profile.data['settings'].get('model', 'gpt-4')],
            LANGUAGE_NAMES[lang_code]
        )
        
        bot.edit_message_text(
            profile_stats, 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu(lang_code)
        )
    elif call.data == 'regenerate_response':
        try:
            new_answer = get_ai_response(
                profile.data['last_message'],
                profile,
                profile.data['settings'].get('model', 'gpt-4'),
                lang_code
            )
            bot.edit_message_text(
                new_answer,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton(get_text(lang_code, 'btn_regenerate'), callback_data='regenerate_response'),
                    types.InlineKeyboardButton(get_text(lang_code, 'btn_modify'), callback_data='modify_response')
                )
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка: {str(e)}")
    elif call.data == 'modify_response':
        bot.edit_message_text(
            get_text(lang_code, 'btn_modify'), 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_modify_response_menu(lang_code)
        )
    elif call.data.startswith('modify_'):
        instruction_map = {
            'modify_shorter': get_text(lang_code, 'modify_shorter'),
            'modify_longer': get_text(lang_code, 'modify_longer'),
            'modify_simpler': get_text(lang_code, 'modify_simpler'),
            'modify_complex': get_text(lang_code, 'modify_complex')
        }
        
        instruction = instruction_map.get(call.data, '')
        
        try:
            modified_answer = get_ai_response(
                f"{instruction}\n\nOriginal text:\n{call.message.text}",
                profile,
                profile.data['settings'].get('model', 'gpt-4'),
                lang_code
            )
            bot.edit_message_text(
                modified_answer,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton(get_text(lang_code, 'btn_regenerate'), callback_data='regenerate_response'),
                    types.InlineKeyboardButton(get_text(lang_code, 'btn_modify'), callback_data='modify_response')
                )
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка: {str(e)}")

bot.message_handler(commands=['start'])(handle_start)
bot.message_handler(func=lambda message: True)(handle_message)
bot.callback_query_handler(func=lambda call: True)(handle_callback)

bot.polling(none_stop=True)