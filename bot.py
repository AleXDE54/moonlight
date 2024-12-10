import telebot
import g4f
import requests
import logging
from telebot import types
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Text Generation Models
TEXT_MODELS = {
    'mixtral': g4f.models.Mixtral,
    'gpt-3.5-turbo': g4f.models.GPT_35_TURBO,
    'claude-v2': g4f.models.Claude_V2,
    'llama-2': g4f.models.Llama2,
    'zephyr': g4f.models.Zephyr
}

# Image Generation Models
IMAGE_MODELS = {
    'flux-pro': 'https://flux-pro-api.com/generate',  # Placeholder, replace with actual API
    'stable-diffusion': 'https://stable-diffusion-api.com/generate',
    'midjourney': 'https://midjourney-api.com/generate',
    'dalle-3': 'https://openai-api.com/dalle3/generate'
}

# Load bot token from config
from config import token

# Initialize bot
bot = telebot.TeleBot(token)

# User state tracking
user_states = {}

def detect_intent(message):
    """
    Use Mixtral to detect user's intent (text or image generation)
    """
    try:
        intent_prompt = f"""
        Analyze the following user message and determine its intent:
        Message: {message}
        
        Respond ONLY with one of these exact keywords:
        - TEXT: If the user wants text generation
        - IMAGE: If the user wants image generation
        - UNKNOWN: If the intent is unclear
        """
        
        intent = g4f.ChatCompletion.create(
            model=g4f.models.Mixtral,
            messages=[{"role": "user", "content": intent_prompt}],
            stream=False
        )
        
        # Clean and validate intent
        intent = intent.strip().upper()
        return intent if intent in ['TEXT', 'IMAGE', 'UNKNOWN'] else 'UNKNOWN'
    
    except Exception as e:
        logger.error(f"Intent detection error: {e}")
        return 'UNKNOWN'

def generate_text(message, model_name='mixtral'):
    """
    Generate text using selected model
    """
    try:
        model = TEXT_MODELS.get(model_name, g4f.models.Mixtral)
        
        response = g4f.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            stream=False
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Text generation error with {model_name}: {e}")
        return "Sorry, I couldn't generate a response."

def generate_image(message, model_name='flux-pro'):
    """
    Generate image using selected model
    """
    try:
        # Placeholder for image generation logic
        # In a real implementation, you'd use specific API calls
        if model_name == 'flux-pro':
            # Example API call (replace with actual implementation)
            response = requests.post('https://flux-pro-api.com/generate', 
                                     json={'prompt': message, 'model': 'default'})
            if response.status_code == 200:
                return response.json().get('image_url')
        
        return "Image generation not fully implemented"
    
    except Exception as e:
        logger.error(f"Image generation error with {model_name}: {e}")
        return "Sorry, I couldn't generate an image."

def create_model_keyboard(model_type):
    """
    Create inline keyboard for model selection
    """
    markup = types.InlineKeyboardMarkup()
    
    if model_type == 'text':
        for model in TEXT_MODELS.keys():
            markup.add(types.InlineKeyboardButton(model.upper(), callback_data=f'text_model_{model}'))
    
    elif model_type == 'image':
        for model in IMAGE_MODELS.keys():
            markup.add(types.InlineKeyboardButton(model.upper(), callback_data=f'image_model_{model}'))
    
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Welcome message and initial instructions
    """
    welcome_text = """
    🤖 Welcome to the Multi-AI Bot! 
    
    I can help you with:
    - Text Generation
    - Image Generation
    
    Just send me a message, and I'll help you choose the right AI model!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Main message handler
    """
    try:
        intent = detect_intent(message.text)
        
        if intent == 'TEXT':
            # Prompt for text model selection
            bot.reply_to(message, 
                         "Choose a text generation model:", 
                         reply_markup=create_model_keyboard('text'))
            user_states[message.from_user.id] = {'intent': 'text', 'message': message.text}
        
        elif intent == 'IMAGE':
            # Prompt for image model selection
            bot.reply_to(message, 
                         "Choose an image generation model:", 
                         reply_markup=create_model_keyboard('image'))
            user_states[message.from_user.id] = {'intent': 'image', 'message': message.text}
        
        else:
            bot.reply_to(message, "I'm not sure what you want. Try being more specific about text or image generation.")
    
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        bot.reply_to(message, "Sorry, something went wrong. Please try again.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Handle model selection callbacks
    """
    try:
        user_id = call.from_user.id
        
        if user_id not in user_states:
            bot.answer_callback_query(call.id, "Session expired. Please start over.")
            return
        
        user_state = user_states[user_id]
        
        if call.data.startswith('text_model_'):
            model = call.data.split('_')[-1]
            response = generate_text(user_state['message'], model)
            bot.send_message(user_id, response)
        
        elif call.data.startswith('image_model_'):
            model = call.data.split('_')[-1]
            response = generate_image(user_state['message'], model)
            
            # Send image or error message
            if response.startswith('http'):
                bot.send_photo(user_id, response)
            else:
                bot.send_message(user_id, response)
        
        # Clear user state after processing
        del user_states[user_id]
        
        bot.answer_callback_query(call.id)
    
    except Exception as e:
        logger.error(f"Callback query error: {e}")
        bot.answer_callback_query(call.id, "An error occurred.")

def main():
    """
    Main bot polling
    """
    logger.info("Bot is running...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()