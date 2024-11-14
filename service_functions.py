import json
import requests


URL = 'https://api.thecatapi.com/v1/images/search'


def load_json_data(file_path):
    """Функция загрузки файла json."""

    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_new_image():
    """Функция получения случайной фотографии котика."""

    response = requests.get(URL).json()
    random_cat = response[0].get('url')
    return random_cat
