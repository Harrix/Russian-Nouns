from pathlib import Path
import json
import re
import requests
import time
import os

dictionary_filename = 'efremova.txt'
dictionary_forms_filename = 'odict.csv'
json_filename = 'data.json'
output_without_filter_json_filename = 'russian_nouns_with_definition_without_filter.json'
output_json_filename = 'russian_nouns_with_definition.json'
output_without_filter_txt_filename = 'russian_nouns_without_filter.txt'
output_txt_filename = 'russian_nouns.txt'
output_with_definition_without_filter_txt_filename = 'russian_nouns_with_definition_without_filter.txt'
output_with_definition_txt_filename = 'russian_nouns_with_definition.txt'


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


def if_exist_dictionary_forms(func):
    def wrapper(*original_args, **original_kwargs):
        file = Path(dictionary_forms_filename)
        if not file.is_file():
            print('Файл {} не существует. Функция не может быть выполнена'.format(dictionary_filename))
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


def index_of(string, substring):
    try:
        index = string.index(substring)
    except ValueError:
        index = -1
    return index


def save_json(dictionary, filename=json_filename):
    file = Path(filename)
    action = 'обновлен' if file.is_file() else 'создан'
    with open(filename, 'w', encoding='utf8') as outfile:
        json.dump(dictionary, outfile, ensure_ascii=False, indent=4)
    print('Файл {} {}'.format(filename, action))


def save_txt(array, filename):
    file = Path(filename)
    action = 'обновлен' if file.is_file() else 'создан'
    with open(filename, 'w', encoding='utf8') as f:
        f.write('\n'.join(array))
    print('Файл {} {}'.format(filename, action))


def read_json(filename=json_filename):
    file = Path(filename)
    with open(file, encoding='utf8') as f:
        dictionary = json.loads(f.read())
    print('Файл {} открыт'.format(filename))
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
    remove(output_without_filter_json_filename)
    remove(output_json_filename)
    remove(output_without_filter_txt_filename)
    remove(output_txt_filename)
    remove(output_with_definition_without_filter_txt_filename)
    remove(output_with_definition_txt_filename)
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
    count_plural_check_need_include = 0
    count_plural_check_include = 0
    count_plural_check_exclude = 0
    count_with_capital_letter = 0
    count_include = 0
    count_exclude = 0

    for word, entry in dictionary.items():
        count += 1
        is_exclude = False
        if 'answerIsProbablyNotNoun' not in entry and 'answerNeedToIncludePlural' not in entry:
            is_include = True
        if 'answerIsProbablyNotNoun' in entry:
            count_check += 1
            if entry['answerIsProbablyNotNoun'] == 'null':
                count_need_check += 1
            if entry['answerIsProbablyNotNoun'] not in ['null', 'noun', 'not noun']:
                count_need_check_404 += 1
            if entry['answerIsProbablyNotNoun'] == 'noun':
                count_need_check_noun += 1
            if entry['answerIsProbablyNotNoun'] == 'not noun':
                count_need_check_not_noun += 1
                is_exclude = True
        if 'answerNeedToIncludePlural' in entry:
            count_plural_check += 1
            if entry['answerNeedToIncludePlural'] == 'null':
                count_plural_need_check += 1
            if entry['answerNeedToIncludePlural'] == 'include':
                count_plural_check_include += 1
            if entry['answerNeedToIncludePlural'] == 'need include':
                count_plural_check_need_include += 1
            if entry['answerNeedToIncludePlural'] == 'exclude':
                count_plural_check_exclude += 1
                is_exclude = True
        if word != word.lower():
            count_with_capital_letter += 1
            is_include = False
            is_exclude = True

        is_noun = True
        if 'answerIsProbablyNotNoun' in entry:
            if entry['answerIsProbablyNotNoun'] != 'noun':
                is_noun = False
        is_plural_include = True
        if 'answerNeedToIncludePlural' in entry:
            if entry['answerNeedToIncludePlural'] != 'include':
                is_plural_include = False

        if is_noun and is_plural_include and word == word.lower():
            count_include += 1
        if is_exclude:
            count_exclude += 1

    print('Всего существительных по Ефремовой: {}'.format(count))
    print('Подозрительные (возможно не сущ.):')
    print('\tвсего: {}'.format(count_check))
    print('\tне проверенные на сайтах: {}'.format(count_need_check))
    print('\tпроверено: {}'.format(count_check - count_need_check))
    print('\tиз них с ошибкой 404 и др.: {}'.format(count_need_check_404))
    print('\tопределено как сущ.: {}'.format(count_need_check_noun))
    print('\tопределено как не сущ.: {}'.format(count_need_check_not_noun))
    print('Слова во множественном числе по Ефремовой:')
    print('\tвсего: {}'.format(count_plural_check))
    print('\tнужно проверить: {}'.format(count_plural_need_check))
    print('\tпроверено: {}'.format(count_plural_check - count_plural_need_check))
    print('\tрекомендуется включить: {}'.format(count_plural_check_need_include))
    print('\tвключаем: {}'.format(count_plural_check_include))
    print('\tисключаем: {}'.format(count_plural_check_exclude))
    print('Слова с большой буквы по Ефремовой:')
    print('\tвсего: {}'.format(count_with_capital_letter))
    print('Итого в итоговый список:')
    print('\tнужно включить: {}'.format(count_include))
    print('\tнужно исключить: {}'.format(count_exclude))
    print('\tнеопределено: {}'.format(count - count_include - count_exclude))


@function_execution_time
@if_exist_json
def print_list_of_words(key, answer, invert=False):
    def print_word():
        print(word)
        print('{} = {}'.format(key, entry[key]))
        print('-------------------------')

    dictionary = read_json()
    count = 0
    for word, entry in dictionary.items():
        if key in entry:
            if not invert:
                if entry[key] in answer:
                    print_word()
                    count += 1
            else:
                if entry[key] not in answer:
                    print_word()
                    count += 1
    print('Слов: {}'.format(count))


@if_exist_json
def print_list_of_words_capital():
    dictionary = read_json()
    count = 0
    for word, entry in dictionary.items():
        if word != word.lower():
            print(word)
            count += 1
    print('Слов: {}'.format(count))


def check_word_in_wiktionary(word, html):
    answer = None

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

    if '<strong>Часть речи</strong>: прилагательное<br />' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: местоимение-существительное<br />' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: числительное' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: наречие' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: деепричастие' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: причастие' in html:
        answer = 'not noun'
    if '<strong>Часть речи</strong>: порядковое числительное' in html:
        answer = 'not noun'

    if '<strong>Часть речи</strong>: существительное<br />' in html:
        answer = 'noun'

    return answer


def check_word_in_morfologija(word, html):
    answer = None

    if '<b>Часть речи:</b> прилагательное' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> наречие' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> местоимение' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> наречие' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> деепричастие' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> поряд. числительное' in html:
        answer = 'not noun'
    if '<b>Часть речи:</b> местоим. прил.' in html:
        answer = 'not noun'

    if '<b>Часть речи:</b> существительное' in html:
        answer = 'noun'

    return answer


def check_word_in_site(word, url, function_check_html):
    answer = None
    response = requests.get(url + word.lower())
    if response.status_code == 200:
        answer_from_html = function_check_html(word, response.text)
        if answer_from_html is not None:
            answer = answer_from_html
    else:
        answer = str(response.status_code)

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
        if 'answerIsProbablyNotNoun' in entry and entry['answerIsProbablyNotNoun'] not in ['noun', 'not noun']:
            try:
                answer = check_word_in_site(word, url, function_check_html)
            except requests.exceptions.ConnectionError:
                print("Ошибка: ConnectionError")
                time.sleep(1)
                save_json(dictionary)
            except requests.exceptions.Timeout:
                print("Ошибка: Timeout")
                time.sleep(10)
                save_json(dictionary)
            if answer is not None:
                dictionary[word]['answerIsProbablyNotNoun'] = answer
                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
    save_json(dictionary)
    print('Проверка слов на {} завершена'.format(url))


def check_plural_word_in_wiktionary(word, html):
    answer = None

    if '<title>{} — Викисловарь</title>'.format(word) in html:
        answer = 'need include'
        if 'формы ед. ч. не используются' in html:
            answer = 'include'
    else:
        if '— Викисловарь</title>'.format(word) in html:
            answer = 'exclude'

    return answer


def check_plural_word_in_goldlit(word, html):
    answer = None

    if '<strong>Начальная форма</strong>: {}'.format(word.upper()) in html:
        answer = 'include'
    else:
        answer = 'exclude'

    return answer


@function_execution_time
@if_exist_json
def check_plural_words_on_site(url, function_check_html):
    dictionary = read_json()
    i = 0
    for word, entry in dictionary.items():
        if 'answerNeedToIncludePlural' in entry and entry['answerNeedToIncludePlural'] not in ['exclude']:
            try:
                answer = check_word_in_site(word, url, function_check_html)
            except requests.exceptions.ConnectionError:
                print("Ошибка: ConnectionError")
                time.sleep(1)
                save_json(dictionary)
            except requests.exceptions.Timeout:
                print("Ошибка: Timeout")
                time.sleep(10)
                save_json(dictionary)
            if answer in ['need include', 'include', 'exclude']:
                dictionary[word]['answerNeedToIncludePlural'] = answer
                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
    save_json(dictionary)
    print('Проверка слов на {} завершена'.format(url))


@function_execution_time
@if_exist_json
def define_words_as_exclude():
    dictionary = read_json()
    for word, entry in dictionary.items():
        if 'answerNeedToIncludePlural' in entry and entry['answerNeedToIncludePlural'] not in ['include']:
            dictionary[word]['answerNeedToIncludePlural'] = 'exclude'
    save_json(dictionary)
    print('Все оставшиеся слова во мн. числе исключены')
    statistics()


@function_execution_time
@if_exist_json
def define_word_as_include():
    dictionary = read_json()
    word = input('Введите слово: ')
    if word in dictionary:
        dictionary[word]['answerNeedToIncludePlural'] = 'include'
        save_json(dictionary)
        print('Слово вручную добавлено')
    else:
        print('Такого слова нет в словаре')


@function_execution_time
@if_exist_json
def define_words_as_nouns():
    dictionary = read_json()
    for word, entry in dictionary.items():
        if 'answerIsProbablyNotNoun' in entry and entry['answerIsProbablyNotNoun'] not in ['noun', 'not noun']:
            dictionary[word]['answerIsProbablyNotNoun'] = 'noun'
    save_json(dictionary)
    print('Все оставшиеся слова определены как сущестуительные')
    statistics()


@function_execution_time
@if_exist_json
@if_exist_dictionary_forms
def check_words_in_plural():
    file = Path(dictionary_forms_filename)
    with open(file) as f:
        dictionary_forms = f.read().splitlines()
    print('Файл {} открыт'.format(dictionary_forms_filename))

    dictionary = read_json()
    for word, entry in dictionary.items():
        if 'answerNeedToIncludePlural' in entry and entry['answerNeedToIncludePlural'] not in ['include', 'exclude']:
            is_initial_form = False
            is_as_form = False
            index_initial_form = -1
            index_as_form = -1
            for index, line in enumerate(dictionary_forms):
                if index_of(line, word + ',') == 0:
                    is_initial_form = True
                    if index_initial_form == -1:
                        index_initial_form = index
                if index_of(line, ',' + word + ',') >= 0:
                    is_as_form = True
                    if index_initial_form != -1 and index_as_form == index_initial_form:
                        index_as_form = index
                    if index_as_form == -1:
                        index_as_form = index
                if line.endswith(',' + word):
                    is_as_form = True
                    if index_initial_form != -1 and index_as_form == index_initial_form:
                        index_as_form = index
                    if index_as_form == -1:
                        index_as_form = index
            answer = None
            if is_initial_form:
                answer = 'need include'
            if not is_initial_form and is_as_form:
                answer = 'exclude'
            if is_initial_form and is_as_form and index_as_form != index_initial_form:
                answer = 'exclude'
            print(word)
            if answer is not None:
                print('answer = {}'.format(answer))
                dictionary[word]['answerNeedToIncludePlural'] = answer
            print('-------------------------')

    save_json(dictionary)
    print('Проверка слов во множественном числе завершена')
    statistics()


@function_execution_time
@if_exist_json
def generate_output():
    dictionary = read_json()
    count_clear = 0
    dictionary_without_filter = {}
    dictionary_clear = {}
    list_without_filter = []
    list_clear = []
    list_with_definition_without_filter = []
    list_with_definition_clear = []
    for word, entry in dictionary.items():
        entry_new = entry.copy()
        if 'answerIsProbablyNotNoun' in entry_new:
            del entry_new['answerIsProbablyNotNoun']
        if 'answerNeedToIncludePlural' in entry_new:
            del entry_new['answerNeedToIncludePlural']
        dictionary_without_filter[word] = entry_new
        list_without_filter.append(word)
        list_with_definition_without_filter.append(word + ': ' + entry['definition'])

        is_noun = True
        if 'answerIsProbablyNotNoun' in entry:
            if entry['answerIsProbablyNotNoun'] != 'noun':
                is_noun = False
        is_plural_include = True
        if 'answerNeedToIncludePlural' in entry:
            if entry['answerNeedToIncludePlural'] != 'include':
                is_plural_include = False

        if is_noun and is_plural_include and word == word.lower():
            count_clear += 1
            dictionary_clear[word] = entry_new
            list_clear.append(word)
            list_with_definition_clear.append(word + ': ' + entry['definition'])

    save_json(dictionary_without_filter, output_without_filter_json_filename)
    save_json(dictionary_without_filter, output_json_filename)

    sorted(list_without_filter)
    sorted(list_clear)
    sorted(list_with_definition_without_filter)
    sorted(list_with_definition_clear)

    save_txt(list_without_filter, output_without_filter_txt_filename)
    save_txt(list_clear, output_txt_filename)
    save_txt(list_with_definition_without_filter, output_with_definition_without_filter_txt_filename)
    save_txt(list_with_definition_clear, output_with_definition_txt_filename)

    print('Слов в файлах без фильтра: {}'.format(len(dictionary_without_filter)))
    print('Слов в отфильтрованных файлах: {}'.format(count_clear))


@if_exist_dictionary
def main():
    menu = [
        {'text': 'Очистить временные файлы', 'function': remove_all_temporary_files},
        {'text': 'Сгенерировать файл {}'.format(json_filename), 'function': generated_json},
        {'text': 'Статистика', 'function': statistics},
        {'text': 'Список непроверенных подозрительных слов', 'function': print_list_of_words,
         'params': {'key': 'answerIsProbablyNotNoun', 'answer': ['null']}},
        {'text': 'Список проверенных подозрительных слов с ошибкой 404 и др.', 'function': print_list_of_words,
         'params': {'key': 'answerIsProbablyNotNoun', 'answer': ['null', 'noun', 'not noun'], 'invert': True}},
        {'text': 'Список непроверенных слов во мн. числе', 'function': print_list_of_words,
         'params': {'key': 'answerNeedToIncludePlural', 'answer': ['null']}},
        {'text': 'Список рекомендуемых к включению слов во мн. числе', 'function': print_list_of_words,
         'params': {'key': 'answerNeedToIncludePlural', 'answer': ['need include']}},
        {'text': 'Список включаемых проверенных слов во мн. числе', 'function': print_list_of_words,
         'params': {'key': 'answerNeedToIncludePlural', 'answer': ['include']}},
        {'text': 'Список невключаемых проверенных слов во мн. числе', 'function': print_list_of_words,
         'params': {'key': 'answerNeedToIncludePlural', 'answer': ['exclude']}},
        {'text': 'Список слов с большой буквы', 'function': print_list_of_words_capital},
        {'text': 'Проверить подозрительные слова на wiktionary.org', 'function': check_words_on_site,
         'params': {'url': 'https://ru.wiktionary.org/wiki/', 'function_check_html': check_word_in_wiktionary}},
        {'text': 'Проверить подозрительные слова на dic.academic.ru', 'function': check_words_on_site,
         'params': {'url': 'https://dic.academic.ru/searchall.php?SWord=',
                    'function_check_html': check_word_in_academic}},
        {'text': 'Проверить подозрительные слова на goldlit.ru', 'function': check_words_on_site,
         'params': {'url': 'https://goldlit.ru/component/slog?words=', 'function_check_html': check_word_in_goldlit}},
        {'text': 'Проверить подозрительные слова на morfologija.ru', 'function': check_words_on_site,
         'params': {'url': 'http://www.morfologija.ru/словоформа/', 'function_check_html': check_word_in_morfologija}},
        {'text': 'Оставшиеся непроверенные слова определить как существительные', 'function': define_words_as_nouns},
        {'text': 'Проверить слова во мн. числе', 'function': check_words_in_plural},
        {'text': 'Проверить слова во мн. числе на wiktionary.org', 'function': check_plural_words_on_site,
         'params': {'url': 'https://ru.wiktionary.org/wiki/', 'function_check_html': check_plural_word_in_wiktionary}},
        {'text': 'Проверить слова во мн. числе на goldlit.ru', 'function': check_plural_words_on_site,
         'params': {'url': 'https://goldlit.ru/component/slog?words=',
                    'function_check_html': check_plural_word_in_goldlit}},
        {'text': 'Определить слово во мн. числе как включаемое', 'function': define_word_as_include},
        {'text': 'Оставшиеся непроверенные слова мн. числе исключить', 'function': define_words_as_exclude},
        {'text': 'Сформировать итоговые файлы', 'function': generate_output},
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
    pass


if __name__ == '__main__':
    main()
