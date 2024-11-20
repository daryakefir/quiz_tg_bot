import random
import threading
import time
from telebot import TeleBot, types, apihelper

from service_functions import load_json_data, get_new_image

bot = TeleBot('YOUR TOKEN')


questions = load_json_data('questions.json')
user_data = {}
timers = {}
max_retries = 5


def safe_send_message(chat_id, text):
    """Функция для безопасной отправки сообщения с обработкой ошибок."""

    retries = 0
    while retries < max_retries:
        try:
            bot.send_message(chat_id, text)
            return
        except apihelper.ApiTelegramException as e:
            if e.error_code == 429:
                wait_time = int(e.result['parameters']['retry_after']) + 1
                time.sleep(wait_time)
                retries += 1
            else:
                break


@bot.message_handler(commands=['newquiz'])
def new_quiz(message):
    """Команда для начала нового квиза."""
    
    chat_id = message.chat.id
    scores = 0
    questions_to_ask = random.sample(questions, 10)
    user_data[chat_id] = {
        'questions': questions_to_ask,
        'current_question_index': 0,
        'scores': scores
    }
    ask_question(chat_id)


def ask_question(chat_id):
    """Функция для отправки вопроса пользователю."""
    
    user_info = user_data.get(chat_id)

    if user_info and user_info['current_question_index'] < len(user_info['questions']):
        question = user_info['questions'][user_info['current_question_index']]
        options = [types.InlineKeyboardButton(option, callback_data=option) for option in question['options']]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*options)

        with open(question['pic'], 'rb') as photo:
            retries = 0
            while retries < max_retries:
                try:
                    bot.send_photo(chat_id=chat_id, photo=photo, reply_markup=keyboard)
                    break  # Успешно отправлено, выходим
                except apihelper.ApiTelegramException as e:
                    if e.error_code == 429:
                        wait_time = 5  # Задержка на 5 секунд (можно изменить)
                        print(f"Бот превысил лимиты, ждем {wait_time} секунд")
                        time.sleep(wait_time)
                        retries += 1
                    else:
                        print(f"Ошибка при отправке фото: {e}")
                        break

        if chat_id in timers:
            timers[chat_id].cancel()
        timers[chat_id] = threading.Timer(30, time_is_up, args=(chat_id,))
        timers[chat_id].start()
    else:
        result = user_info['scores']
        safe_send_message(chat_id, f'Your result is {result} from 10 🐥!')
        safe_send_message(chat_id, get_new_image())
        del user_data[chat_id]
        if chat_id in timers:
            timers[chat_id].cancel()
            del timers[chat_id]


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Функция для обработки нажатия кнопки ответа пользователем."""
    
    chat_id = call.message.chat.id
    user_info = user_data.get(chat_id)

    if user_info:
        question = user_info['questions'][user_info['current_question_index']]
        is_correct = call.data == question['answer']
        response_text = 'Right!' if is_correct else 'Wrong!'

        # Используем безопасную функцию отправки
        bot.answer_callback_query(call.id, text=response_text)

        user_info['scores'] += 1 if is_correct else 0
        user_info['current_question_index'] += 1
        ask_question(chat_id)


def time_is_up(chat_id):
    """Функция для обработки истечения времени ожидания ответа."""

    user_info = user_data.get(chat_id)
    if user_info:
        safe_send_message(chat_id=chat_id, text='Time is over!')
        user_info['current_question_index'] += 1
        ask_question(chat_id)


@bot.message_handler(commands=['start'])
@bot.message_handler(content_types=['text'])
def wake_up(message):
    chat = message.chat
    name = message.chat.first_name
    keyboard = types.ReplyKeyboardMarkup()
    button_newquiz = types.KeyboardButton('/newquiz')
    keyboard.add(button_newquiz)

    safe_send_message(chat_id=chat.id, text=f'Hello, {name}! '
                                            'Do you wanna play the quiz about Solidity❔❔❔ \n'
                                            'There will be 10 questions with 30 seconds for each. \n'
                                            'A very special surprise awaits you at the end of quiz! 🎁 \n'
                                            'Push /newquiz 👣')

bot.polling()
