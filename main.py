import argparse
import os
import sqlite3

import requests
from bs4 import BeautifulSoup

import validators

number_of_pages_to_search = 3
database_name = 'urls.db'


def req(query, urls_to_find):
    urls_from_search = []
    for page in range(number_of_pages_to_search):
        url = f'http://yandex.ru/yandsearch?text=%(q)s&p={page}'
        payload = {'q': query, }
        r = requests.get(url % payload)
        soup = BeautifulSoup(r.text, features="html.parser")
        all_target_divs = soup.findAll('div', attrs={"class": "path path_show-https organic__path"})
        urls_from_search.extend([item.a['href'] for item in all_target_divs])

    if not urls_from_search:
        raise Exception("Urls not found in search results")

    print(f'search returned {len(urls_from_search)} urls')

    found_urls = [(index, url) for index, url in enumerate(urls_from_search) if url in urls_to_find]
    print(f'{len(found_urls)} of {len(urls_to_find)} found')
    return found_urls


def create_database():
    src_to_db = os.path.join(os.path.dirname(__file__), database_name)  # pragma: no cover

    try:
        os.remove(src_to_db)
        print('old database file removed')
    except FileNotFoundError:
        print('there is no old file of database to remove')
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    try:
        cursor.execute("""CREATE TABLE urls (url text, number int) """)
        conn.commit()
        print(f'database {database_name} created')
        return conn
    except sqlite3.OperationalError as e:
        print(f'database is not created due to error: {e}')
        raise


def save(conn, data):
    try:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO urls VALUES (?,?)", data)
        conn.commit()
        print(f'data added to {database_name}')
    except sqlite3.OperationalError as e:
        print(f'urls not added to database due to error: {e}')


def parse_arguments():
    parser = argparse.ArgumentParser(description='Find position of url in yandex')
    parser.add_argument('query', type=str, nargs="+",
                        help='query to search in string format')
    parser.add_argument('--url', type=str, action='append', required=True,
                        help='url to find in search results, in string, you may add more than one url')
    args = vars(parser.parse_args())
    query = ' '.join(args['query'])
    urls = args['url']
    for url in urls:

        valid = validators.url(url)
        if valid is not True:
            raise Exception(f"{url} is not valid url")

    return query, urls


if __name__ == '__main__':
    query, urls = parse_arguments()
    data = req(query=query, urls_to_find=urls)
    connection = create_database()

    save(conn=connection, data=data)
