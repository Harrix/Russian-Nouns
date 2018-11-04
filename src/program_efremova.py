from pathlib import Path
import json
import re
import requests
import time
import os

dictionary_filename = 'efremova.txt'
json_filename = 'data.json'


def if_exist_dictionary(func):
    def wrapper(*original_args, **original_kwargs):
        file = Path(dictionary_filename)
        if not file.is_file():
            print('Файл {} не существует. Программа не может быть выполнена'.format(dictionary_filename))
            return
        func(*original_args, **original_kwargs)

    return wrapper


def if_exist_json(func):
    def wrapper(*original_args, **original_kwargs):
        file = Path(json_filename)
        if not file.is_file():
            print('Файл {} не существует. Его нужно сгенерировать первоначально'.format(json_filename))
            return
        func(*original_args, **original_kwargs)

    return wrapper


def function_execution_time(func):
    def wrapper(*original_args, **original_kwargs):
        start = time.time()
        func(*original_args, **original_kwargs)
        end = time.time()
        print('Время выполнения функции: {}\n'.format(time.strftime('%H:%M:%S', time.gmtime(end - start))))

    return wrapper


def save_json(dictionary):
    file = Path(json_filename)
    action = 'обновлен' if file.is_file() else 'создан'
    with open(json_filename, 'w', encoding='utf8') as outfile:
        json.dump(dictionary, outfile, ensure_ascii=False, indent=4)
    print('Файл {} {}'.format(json_filename, action))


def read_json():
    file = Path(json_filename)
    with open(file, encoding='utf8') as f:
        dictionary = json.loads(f.read())
    print('Файл {} открыт'.format(json_filename))
    return dictionary


@function_execution_time
def remove_all_temporary_files():
    def remove(filename):
        if Path(json_filename).is_file():
            os.remove(json_filename)
            print('Файл {} удален'.format(json_filename))
        else:
            print('Файл {} не существует'.format(json_filename))

    remove(json_filename)
    print('Временных файлов больше нет')


@function_execution_time
@if_exist_dictionary
def generated_json():
    file = Path(dictionary_filename)
    with open(file, encoding='utf8') as f:
        lines = f.read().splitlines()
    dictionary = {}
    for line in lines:
        word = line.split(' ', 1)[0]
        definition = line.split(' ', 1)[1]
        if not bool(re.match(r'(ж|м|ср|мн)\.(.*)$', definition) or re.match(r'(1\.|I) (ж|м|ср|мн)\.(.*)$', definition)):
            continue
        dictionary[word] = {'definition': definition}
        if word[-2:] in ['ая', 'ее', 'ие', 'ий', 'ое', 'ой', 'ые', 'ый', 'ье', 'ьи', 'ья', 'яя']:
            dictionary[word]['answerIsProbablyNotNoun'] = 'null'
        if bool(re.match(r'(мн)\.(.*)$', definition) or re.match(r'(1\.|I) (мн)\.(.*)$', definition)):
            dictionary[word]['answerNeedToIncludePlural'] = 'null'
    save_json(dictionary)


@function_execution_time
@if_exist_json
def statistics():
    dictionary = read_json()
    count = 0
    count_check = 0
    count_need_check = 0
    count_need_check_404 = 0
    count_need_check_noun = 0
    count_need_check_not_noun = 0
    count_plural_check = 0
    count_plural_need_check = 0

    for word, entry in dictionary.items():
        count += 1
        if 'answerIsProbablyNotNoun' in entry:
            count_check += 1
            if entry['answerIsProbablyNotNoun'] == 'null':
                count_need_check += 1
            if entry['answerIsProbablyNotNoun'] == '404':
                count_need_check_404 += 1
            if entry['answerIsProbablyNotNoun'] == 'noun':
                count_need_check_noun += 1
            if entry['answerIsProbablyNotNoun'] == 'not noun':
                count_need_check_not_noun += 1
        if 'answerNeedToIncludePlural' in entry:
            count_plural_check += 1
            if entry['answerNeedToIncludePlural'] == 'null':
                count_plural_need_check += 1

    print('Всего существительных по Ефремовой: {}'.format(count))
    print('Подозрительные (возможно не сущ.):')
    print('\tвсего: {}'.format(count_check))
    print('\tне проверенные на сайтах: {}'.format(count_need_check))
    print('\tпроверено: {}'.format(count_check - count_need_check))
    print('\tиз них с ошибкой 404: {}'.format(count_need_check_404))
    print('\tопределено как сущ.: {}'.format(count_need_check_noun))
    print('\tопределено как не сущ.: {}'.format(count_need_check_not_noun))
    print('Слова во множественном числе по Ефремовой:')
    print('\tвсего: {}'.format(count_plural_check))
    print('\tнужно проверить: {}'.format(count_plural_need_check))
    print('\tпроверено: {}'.format(count_plural_check - count_plural_need_check))


@function_execution_time
@if_exist_json
def print_list_of_words(key, answer):
    def print_word():
        print(word)
        print('{} = {}'.format(key, entry[key]))
        print('-------------------------')

    dictionary = read_json()
    count = 0
    for word, entry in dictionary.items():
        if key in entry:
            if entry[key] == answer:
                print_word()
                count += 1

    print('Слов: {}'.format(count))


def check_word_in_wiktionary(word, html):
    answer = None

    if '<title>{} — Викисловарь</title>'.format(word) not in html:
        return '404';

    if 'title="существительное">Существительное</a>' in html:
        answer = 'noun'
    if 'Существительное.' in html:
        answer = 'noun'
    if 'title="выступает в роли существительного">субстантивир.</span>' in html:
        answer = 'noun'
    if 'Существительное' in html and 'Прилагательное' not in html:
        answer = 'noun'
    if 'Существительное, одушевлённое,  тип склонения по ' in html:
        answer = 'noun'

    if 'title="прилагательное">Прилагательное</a>' in html:
        answer = 'not noun'
    if 'title="причастие">Причастие</a>' in html:
        answer = 'not noun'
    if 'title="причастие">причастие</a>' in html:
        answer = 'not noun'
    if 'title="наречие">Наречие</a>' in html:
        answer = 'not noun'
    if 'title="деепричастие">деепричастие</a>' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Прилагательное' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'прилагательного' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Местоименное прилагательное' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Притяжательное местоимение' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Притяжательное прилагательное' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Числительное' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Порядковое числительное' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Местоимение' in html:
        answer = 'not noun'
    if 'Существительное' not in html and 'Указательное местоимение' in html:
        answer = 'not noun'

    return answer


def check_word_in_academic(word, html):
    answer = None
    regexp = r'</a><\/strong> — сущ\.(.*?)<\/p>\n<p class="src">' \
             r'<a href="\/\/dic\.academic\.ru\/contents.nsf\/dic_synonims\/">Словарь синонимов<\/a><\/p>'
    if re.search(re.escape(word) + regexp, html, re.S):
        answer = 'noun'
    return answer


def check_word_in_goldlit(word, html):
    answer = None

    if '<title>Морфологический разбор слова: {}</title>'.format(word) not in html:
        return '404'

    if '<strong>Часть речи</strong>: существительное<br />' in html:
        answer = 'noun'

    if '<strong>Часть речи</strong>: прилагательное<br />' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: местоимение-существительное<br />' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: числительное' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: наречие' in html:
        answer = 'not noun'

    return answer


def check_word_in_site(word, url, function_check_html):
    answer = None
    try:
        response = requests.get(url + word, allow_redirects=False)
        if response.status_code == 200:
            answer_from_html = function_check_html(word, response.text)
            if answer_from_html is not None:
                answer = answer_from_html
        else:
            answer = str(response.status_code)
    except ConnectionError:
        print("Ошибка: ConnectionError")
        time.sleep(1)
    print('word = {}'.format(word))
    print('answer = {}'.format(answer))
    print('-------------------------')
    return answer


@function_execution_time
@if_exist_json
def check_words_on_site(url, function_check_html):
    dictionary = read_json()
    i = 0
    for word, entry in dictionary.items():
        if 'answerIsProbablyNotNoun' in entry and entry['answerIsProbablyNotNoun'] in ['null', '404']:
            answer = check_word_in_site(word, url, function_check_html)
            if answer is not None:
                dictionary[word]['answerIsProbablyNotNoun'] = answer
                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
    save_json(dictionary)
    print('Проверка слов на {} завершена'.format(url))


@if_exist_dictionary
def main():
    menu = [
        {'text': 'Очистить временные файлы', 'function': remove_all_temporary_files},
        {'text': 'Сгенерировать файл {}'.format(json_filename), 'function': generated_json},
        {'text': 'Статистика', 'function': statistics},
        {'text': 'Список непроверенных подозрительных слов', 'function': print_list_of_words,
         'params': {'key': 'answerIsProbablyNotNoun', 'answer': 'null'}},
        {'text': 'Список проверенных подозрительных слов с ошибкой 404', 'function': print_list_of_words,
         'params': {'key': 'answerIsProbablyNotNoun', 'answer': '404'}},
        {'text': 'Список непроверенных слов во мн. числе', 'function': print_list_of_words,
         'params': {'key': 'answerNeedToIncludePlural', 'answer': 'null'}},
        {'text': 'Проверить подозрительные слова на wiktionary.org', 'function': check_words_on_site,
         'params': {'url': 'https://ru.wiktionary.org/wiki/', 'function_check_html': check_word_in_wiktionary}},
        {'text': 'Проверить подозрительные слова на dic.academic.ru', 'function': check_words_on_site,
         'params': {'url': 'https://dic.academic.ru/searchall.php?SWord=',
                    'function_check_html': check_word_in_academic}},
        {'text': 'Проверить подозрительные слова на goldlit.ru', 'function': check_words_on_site,
         'params': {'url': 'https://goldlit.ru/component/slog?words=', 'function_check_html': check_word_in_goldlit}},
    ]

    while True:
        for index, item in enumerate(menu):
            print('{} - {}'.format(index + 1, item['text']))
        try:
            command = int(input('Введите номер команды (нажмите Enter для выхода): '))
        except ValueError:
            break
        if command > len(menu) or command < 0:
            break
        if 'params' not in menu[command - 1]:
            menu[command - 1]['function']()
        else:
            menu[command - 1]['function'](**menu[command - 1]['params'])
        input("Нажмите Enter для продолжения...")


def test():
    answer = check_word_in_site('мост', 'https://dic.academic.ru/searchall.php?SWord=', check_word_in_academic)
    print(answer)


if __name__ == '__main__':
    main()
