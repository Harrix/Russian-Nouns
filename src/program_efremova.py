from pathlib import Path
import json
import re
import requests
import time
import os

dictionary_filename = 'efremova.txt'
dictionary_json_filename = 'data.json'


def if_exist_dictionary(func):
    def wrapper():
        file = Path(dictionary_filename)
        if not file.is_file():
            print('Файл {} не существует. Программа не может быть выполнена'.format(dictionary_filename))
            return
        func()

    return wrapper


def if_exist_json(func):
    def wrapper():
        file = Path(dictionary_json_filename)
        if not file.is_file():
            print('Файл {} не существует. Его нужно сгенерировать первоначально'.format(dictionary_json_filename))
            return
        func()

    return wrapper


def function_execution_time(func):
    def wrapper():
        start = time.time()
        func()
        end = time.time()
        print('Время выполнения функции: {}'.format(time.strftime('%H:%M:%S', time.gmtime(end - start))))

    return wrapper


@if_exist_dictionary
def main():
    menu = [
        {'text': 'Очистить временные файлы', 'function': clear_all_temporary_files},
        {'text': 'Сгенерировать файл {}'.format(dictionary_json_filename), 'function': generated_json},
        {'text': 'Сколько слов нужно проверить на сайтах', 'function': how_many_articles_need_to_check},
        {'text': 'Вывести список непроверенных слов (answer_from_sites = null)',
         'function': print_list_of_words, 'params': 'null'},
        {'text': 'Вывести список непроверенных слов c ошибкой 404  (answer_from_sites = 404)',
         'function': print_list_of_words, 'params': '404'},
        {'text': 'Проверить подозрительные слова на сайтах', 'function': check_words_on_sites}
    ]

    while True:
        print('')
        for index, item in enumerate(menu):
            print('{} - {}'.format(index + 1, item['text']))
        command = int(input('Введите номер команды (любой другой номер завершит программу): '))
        if command > len(menu) or command < 0:
            break
        if 'params' not in menu[command - 1]:
            menu[command - 1]['function']()
        else:
            menu[command - 1]['function'](menu[command - 1]['params'])


@function_execution_time
def clear_all_temporary_files():
    def delete_file(filename):
        if Path(dictionary_json_filename).is_file():
            os.remove(dictionary_json_filename)
            print('Файл {} удален'.format(dictionary_json_filename))
        else:
            print('Файл {} не существует'.format(dictionary_json_filename))

    delete_file(dictionary_json_filename)
    print('Временных файлов больше нет')


@function_execution_time
@if_exist_dictionary
def generated_json():
    file = Path(dictionary_filename)
    with open(file, encoding='utf8') as f:
        lines = f.read().splitlines()
    dictionary = dict()
    for line in lines:
        split_line = line.split(' ', 1)
        word = split_line[0]
        definition = split_line[1]

        is_noun_by_dictionary = False
        if re.match(r'(ж|м|ср|мн)\.(.*)$', definition) or re.match(r'(1\.|I) (ж|м|ср|мн)\.(.*)$', definition):
            is_noun_by_dictionary = True

        is_possible_not_noun = False
        if (
                word.endswith('ая') or
                word.endswith('ее') or
                word.endswith('ие') or
                word.endswith('ий') or
                word.endswith('ое') or
                word.endswith('ой') or
                word.endswith('ые') or
                word.endswith('ый') or
                word.endswith('ье') or
                word.endswith('ьи') or
                word.endswith('ья') or
                word.endswith('яя')
        ):
            is_possible_not_noun = True

        entry = dict()
        entry['definition'] = definition
        entry['is_noun_by_dictionary'] = is_noun_by_dictionary
        entry['is_possible_not_noun'] = is_possible_not_noun
        entry['answer_from_sites'] = 'null'
        dictionary[word] = entry

    save_json(dictionary)


@function_execution_time
@if_exist_dictionary
def how_many_articles_need_to_check():
    dictionary = read_json()

    count_all = 0
    count_nouns_by_dictionary = 0
    count_check = 0
    for word, entry in dictionary.items():
        count_all += 1
        if entry['is_noun_by_dictionary']:
            count_nouns_by_dictionary += 1
        if (
                entry['is_noun_by_dictionary'] and
                entry['is_possible_not_noun'] and
                entry['answer_from_sites'] == 'null'
        ):
            count_check += 1

    print('Все слова: {}'.format(count_all))
    print('Количество существительных по Ефремовой: {}'.format(count_nouns_by_dictionary))
    print('Нужно проверить на сайтах: {}'.format(count_check))


@function_execution_time
@if_exist_json
def print_list_of_words(answer_from_sites):
    dictionary = read_json()

    count = 0
    for word, entry in dictionary.items():
        if entry['is_noun_by_dictionary'] and entry['is_possible_not_noun']:
            is_print = False

            if answer_from_sites == 'null' and entry['answer_from_sites'] == 'null':
                is_print = True

            if answer_from_sites == '404' and entry['answer_from_sites'] == 404:
                is_print = True

            if is_print:
                print(word)
                print('answer_from_sites = {}'.format(entry['answer_from_sites']))
                print('-------------------------')
                count += 1

    print('Слов: {}'.format(count))


@function_execution_time
@if_exist_json
def check_words_on_sites():
    dictionary = read_json()

    i = 0
    for word, entry in dictionary.items():
        if (
                entry['is_noun_by_dictionary'] and
                entry['is_possible_not_noun'] and
                entry['answer_from_sites'] == 'null'
        ):
            try:
                response = requests.get('https://ru.wiktionary.org/wiki/' + word)
                print('{} status_code = {}'.format(word, response.status_code))
                if response.status_code == 200:
                    html = response.text
                    is_noun_by_wiktionary = False
                    is_not_noun_by_wiktionary = False
                    if (
                            'title="существительное">Существительное</a>' in html or
                            'Существительное.' in html or
                            'title="выступает в роли существительного">субстантивир.</span>' in html or
                            ('Существительное' in html and 'Прилагательное' not in html) or
                            'Существительное, одушевлённое,  тип склонения по ' in html
                    ):
                        is_noun_by_wiktionary = True

                    if (
                            'title="прилагательное">Прилагательное</a>' in html or
                            'title="причастие">Причастие</a>' in html or
                            'title="причастие">причастие</a>' in html or
                            'title="наречие">Наречие</a>' in html or
                            'title="деепричастие">деепричастие</a>' in html or
                            ('Существительное' not in html and 'Прилагательное' in html) or
                            ('Существительное' not in html and 'прилагательного' in html) or
                            ('Существительное' not in html and 'Местоименное прилагательное' in html) or
                            ('Существительное' not in html and 'Притяжательное местоимение' in html) or
                            ('Существительное' not in html and 'Притяжательное прилагательное' in html) or
                            ('Существительное' not in html and 'Числительное' in html) or
                            ('Существительное' not in html and 'Порядковое числительное' in html) or
                            ('Существительное' not in html and 'Местоимение' in html) or
                            ('Существительное' not in html and 'Указательное местоимение' in html)
                    ):
                        is_not_noun_by_wiktionary = True

                    if is_noun_by_wiktionary:
                        dictionary[word]['answer_from_sites'] = 'noun'
                        print('answer_from_sites = noun')

                    if is_not_noun_by_wiktionary:
                        dictionary[word]['answer_from_sites'] = 'not_noun'
                        print('answer_from_sites = not_noun')

                    if not is_noun_by_wiktionary and not is_not_noun_by_wiktionary:
                        print('Need more checks')
                else:
                    dictionary[word]['answer_from_sites'] = response.status_code
                    print('url = {}'.format(response.url))
                print('-------------------------')

                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
            except ConnectionError:
                print("Error: ConnectionError")
                time.sleep(1)

    i = 0
    for word, entry in dictionary.items():
        if (
                entry['is_noun_by_dictionary'] and
                entry['is_possible_not_noun'] and
                entry['answer_from_sites'] == 404
        ):
            try:
                response = requests.get('https://dic.academic.ru/searchall.php?SWord=' + word)
                print('{} status_code = {}'.format(word, response.status_code))
                if response.status_code == 200:
                    html = response.text
                    is_noun_by_wiktionary = False
                    is_not_noun_by_wiktionary = False

                    if re.search(
                            re.escape(
                                word) + r'</a><\/strong> — сущ\.(.*?)<\/p>\n<p class="src"><a href="\/\/dic\.academic\.ru\/contents.nsf\/dic_synonims\/">Словарь синонимов<\/a><\/p>',
                            html, re.S):
                        is_noun_by_wiktionary = True

                    if is_noun_by_wiktionary:
                        dictionary[word]['answer_from_sites'] = 'noun'
                        print('answer_from_sites = noun')

                    # if is_not_noun_by_wiktionary:
                    #     dictionary[word]['answer_from_sites'] = 'not_noun'
                    #     print('answer_from_sites = not_noun')

                    if not is_noun_by_wiktionary:
                        print('Need more checks')
                print('-------------------------')

                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
            except ConnectionError:
                print("Ошибка: ConnectionError")
                time.sleep(1)

    save_json(dictionary)
    print('Проверка подозрительных слов завершена')


def save_json(dictionary):
    file = Path(dictionary_json_filename)
    action = 'обновлен' if file.is_file() else 'создан'
    with open(dictionary_json_filename, 'w', encoding='utf8') as outfile:
        json.dump(dictionary, outfile, ensure_ascii=False, indent=4)
    print('Файл {} {}'.format(dictionary_json_filename, action))


def read_json():
    file = Path(dictionary_json_filename)
    with open(file, encoding='utf8') as f:
        dictionary = json.loads(f.read())
    print('Файл ' + dictionary_json_filename + ' открыт')
    return dictionary


def test():
    # print(urllib.parse.quote_plus('безносая', safe=''))
    pass


if __name__ == '__main__':
    main()