from pathlib import Path
import json
import re
import requests
import time
import os

dictionary_filename = 'efremova.txt'
dictionary_json_filename = 'data.json'
url = 'https://ru.wiktionary.org/wiki/'


def main():
    if not is_exist_dictionary():
        return

    while True:
        print('')
        print('1 - Clear all temporary files')
        print('2 - Generated file {}'.format(dictionary_json_filename))
        print('3 - How many articles need to check on {}'.format(url))
        print('4 - Check the words on {}'.format(dictionary_json_filename))
        print('5 - Print a list of unchecked words on {}'.format(dictionary_json_filename))
        print('6 - Print a list of words on {} with 404 error'.format(dictionary_json_filename))
        print('10 - Exit')

        command = int(input('Enter command number '))
        if command == 1:
            clear_all_temporary_files()
        if command == 2:
            generated_json()
        if command == 3:
            how_many_articles_need_to_check()
        if command == 4:
            check_words_on_site()
        if command == 5:
            print_list_of_words('null')
        if command == 6:
            print_list_of_words('404')
        if command == 10:
            break


def clear_all_temporary_files():
    start = time.time()
    file = Path(dictionary_json_filename)
    if file.is_file():
        os.remove(dictionary_json_filename)
    print('All temporary files deleted')
    end = time.time()
    print_time(start, end)


def generated_json():
    start = time.time()
    if not is_exist_dictionary():
        return

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

        is_possible_adjective = False
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
            is_possible_adjective = True

        entry = dict()
        entry['definition'] = definition
        entry['is_noun_by_dictionary'] = is_noun_by_dictionary
        entry['is_possible_adjective'] = is_possible_adjective
        entry['answer_from_wiktionary'] = 'null'
        dictionary[word] = entry

    save_json(dictionary)
    end = time.time()
    print_time(start, end)


def how_many_articles_need_to_check():
    start = time.time()
    if not is_exist_json():
        return
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
                entry['is_possible_adjective'] and
                entry['answer_from_wiktionary'] == 'null'
        ):
            count_check += 1

    print('All words: {}'.format(count_all))
    print('All nouns by dictionary: {}'.format(count_nouns_by_dictionary))
    print('It remains to check words: {}'.format(count_check))
    end = time.time()
    print_time(start, end)


def print_list_of_words(answer_from_wiktionary):
    start = time.time()
    if not is_exist_json():
        return
    dictionary = read_json()

    count = 0
    for word, entry in dictionary.items():
        if entry['is_noun_by_dictionary'] and entry['is_possible_adjective']:
            is_print = False

            if answer_from_wiktionary == 'null' and entry['answer_from_wiktionary'] == 'null':
                is_print = True

            if answer_from_wiktionary == '404' and entry['answer_from_wiktionary'] == 404:
                is_print = True

            if is_print:
                print(word)
                print('answer_from_wiktionary = {}'.format(entry['answer_from_wiktionary']))
                print('-------------------------')
                count += 1

    print('Words: {}'.format(count))
    end = time.time()
    print_time(start, end)


def check_words_on_site():
    start = time.time()
    if not is_exist_json():
        return
    dictionary = read_json()

    i = 0
    for word, entry in dictionary.items():
        if (
                entry['is_noun_by_dictionary'] and
                entry['is_possible_adjective'] and
                entry['answer_from_wiktionary'] == 'null'
        ):
            try:
                response = requests.get(url + word)
                print('{} status_code = {}'.format(word, response.status_code))
                if response.status_code == 200:
                    html = response.text
                    is_noun_by_wiktionary = False
                    is_adjective_by_wiktionary = False
                    if 'title="существительное">Существительное</a>' in html:
                        is_noun_by_wiktionary = True
                    if 'title="выступает в роли существительного">субстантивир.</span>' in html:
                        is_noun_by_wiktionary = True
                    if 'Существительное' in html and 'Прилагательное' not in html:
                        is_noun_by_wiktionary = True

                    if 'title="прилагательное">Прилагательное</a>' in html:
                        is_adjective_by_wiktionary = True
                    if 'Существительное' not in html and 'Прилагательное' in html:
                        is_adjective_by_wiktionary = True

                    if is_noun_by_wiktionary:
                        dictionary[word]['answer_from_wiktionary'] = 'noun'
                        print('answer_from_wiktionary = noun')

                    if is_adjective_by_wiktionary:
                        dictionary[word]['answer_from_wiktionary'] = 'adjective'
                        print('answer_from_wiktionary = adjective')

                    if not is_noun_by_wiktionary and not is_adjective_by_wiktionary:
                        print('Need more checks')
                else:
                    dictionary[word]['answer_from_wiktionary'] = response.status_code
                    print('url = {}'.format(response.url))
                print('-------------------------')

                i += 1
                if i % 100 == 0:
                    save_json(dictionary)
            except ConnectionError:
                print("Error: ConnectionError")
                time.sleep(1)

    save_json(dictionary)
    print('Analysis of a dictionary using the {} ended'.format(url))
    end = time.time()
    print_time(start, end)


def print_time(start, end):
    print('Function execution time: {}'.format(end - start))


def save_json(dictionary):
    file = Path(dictionary_json_filename)
    action = 'updated' if file.is_file() else 'created'
    with open(dictionary_json_filename, 'w', encoding='utf8') as outfile:
        json.dump(dictionary, outfile, ensure_ascii=False, indent=4)
    print('File {} {}'.format(dictionary_json_filename, action))


def read_json():
    file = Path(dictionary_json_filename)
    with open(file, encoding='utf8') as f:
        dictionary = json.loads(f.read())
    print('File ' + dictionary_json_filename + ' opened')
    return dictionary


def is_exist_json():
    file = Path(dictionary_json_filename)
    if not file.is_file():
        print('File {} not exists. This file needs to be generated.'.format(dictionary_json_filename))
    return file.is_file()


def is_exist_dictionary():
    file = Path(dictionary_filename)
    if not file.is_file():
        print('File {} not exists. The program cannot work.'.format(dictionary_filename))
    return file.is_file()


def test():
    pass


if __name__ == '__main__':
    main()
