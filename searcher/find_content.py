from bs4 import BeautifulSoup
import requests
import re
import sqlite3

connect = sqlite3.connect('../subtitles.db')
cur = connect.cursor()

def dict_factory(cursor, row):
    """
    Оберка над sqlite для перевода в словарь
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def find_text(text):
    """
    Поиск слова и фраз в базе данных
    """
    connect = sqlite3.connect('../subtitles.db')
    connect.row_factory = dict_factory
    words_dict = connect.execute(f"""select * from subtitles where content like '% {text} %' ;""")
    return words_dict.fetchall()

def find_video(id: int):
    """
    Поиск ссылки для загрузки на сайт по id видео
    """
    soup = BeautifulSoup(requests.get(f'https://www.ted.com/talks/{id}').content, features="html.parser")

    for video_link in soup.find_all("script"):
        video_link = str(video_link)
        if re.search("__NEXT_DATA__", video_link):
            video_data = video_link
            result_mp4 = re.search("(?P<url>https?://[^\s]+.mp4)", video_data)[1]

            return result_mp4


def get_content(words: str):
    """
    Выдает список словарей с данными о нашем слове
    """
    results = find_text(words)
    return results


def get_definition(search_word: str):
    """
    Парсит сайт-словарь woordhunt и выдает определения слова
    """
    soup = BeautifulSoup(requests.get(f'https://wooordhunt.ru/word/{search_word}').content, features="html.parser")
    word_definition_path = 'Слово не имеет значения'
    for link in soup.find_all("div"):
        link = str(link)
        if re.search("t_inline_en", link):
            word_definition_path = link
            word_definition_path = word_definition_path.replace('<', '(')
            word_definition_path = word_definition_path.replace('>', ')')

    word_definition = re.sub(r'\([^\)]+\)', '', word_definition_path)

    return word_definition


def get_video(content):
    """
    Режет видео с фразой с добавкой 100мкс и выдает на сайт
    На сайте выводиться только 5 видео на старницу  можно и больше
    возвращает слоаврь: ключ-номер примера в видео,значение-лист состоящий из субтитров и ссылки на видео
    Видео выводяться разные.Я поставил проверку на id видео,чтобы они были разные
    """
    data_video_frame = {}
    information_array = []
    counter = 0
    old_id = -1
    for data_dict in content:
        if old_id == data_dict['video_Id']:
            continue
        old_id = data_dict['video_Id']
        result_mp4 = find_video(data_dict['video_Id'])
        if result_mp4 is None:
            continue
        result_mp4_link = result_mp4 + f'#t={data_dict["startTime"]/1000},' \
                                       f'{(data_dict["startTime"] + data_dict["duration"] +100)/1000}'
        information_array.append(result_mp4_link)
        counter += 1
        information_array.append(data_dict['content'])
        data_video_frame[counter] = information_array.copy()
        information_array.clear()
        if counter == 5:
            return data_video_frame
    return data_video_frame


connect.close()
