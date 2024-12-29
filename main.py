#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt


# Tasks:
# 1) Шукай:
# # Саме тут слід прописати перевірку на унікальність доданих ID кожної картки

# 2) Порівняй ціни на товари з однаковими вагою / назвами

# 3) Виведи частотність назв підгруп, а саме:
# чого найбільше зустрічається в асортименті, - молока, кефіру, масла чи чогось іншого?..

# 4) З'ясуй, чому для деяких товарів не пораховане значення price_per_weightм,
#  - при існуючих відповідних значеннях current_price та volume_part

# 5) З'ясуй, які продукти є найдорожчими за 1 кг / 1 л

# !!!
# Поки варто зробити так:
# 1) Зібрати дані з усіх категорій Сільпо (може, ще й з кожного міста)
# 2) Зібрати дані з інших маркетів
# 3) Створити таблицю(ці) з унормованими даними (тобто, цінами за кг/л/шт тощо)

# !!!
# Власне API сайту silpo:
#     https://sf-ecom-api.silpo.ua/v1/uk/branches/00000000-0000-0000-0000-000000000000/products?limit=200&deliveryType=DeliveryHome&sortBy=popularity&sortDirection=desc&mustHavePromotion=true&inStock=true
# !!!
# Знайшов!)
# Також почитай поради від ChatGPT

# 1) Потренуватись в роботі з гілками
# git merge local remoute server

# 1) Зібрати вручну список API-адрес
# 2) Парсером зібрати усі дані з них
# 3) Додати до кожного продукту його вартість за 1 кг / л / упаковку тощо відповідно


import requests, time, csv, logging, socket, json, sys
from bs4 import BeautifulSoup
from functools import lru_cache

from pathlib import Path

from iteration_utilities import duplicates

from collections import Counter

import os.path

# ---------- Utility functions --------------------
def is_connected():    # Для перевірки доступності інтернету перед відправленням запиту
    try:
        socket.create_connection(('www.google.com', 80), timeout=5)
        return True
    except OSError:
        return False


def get_file_path(fname):       # Визначаємо повний шлях до файлу fname
    return Path(__file__).parent / fname


def handle_exception(e, context=""):
    """
    Handles exceptions and returns a formatted error message.

    Args:
        e (Exception): The exception to handle.
        context (str): Additional context about where the error occurred.

    Returns:
        str: Formatted error message
    """
    error_messages = {
        requests.exceptions.Timeout: "Request timed out.",
        requests.exceptions.ConnectionError: "Could not connect to the server.",
        requests.exceptions.HTTPError: "HTTP error occurred.",
        AttributeError: "HTML structure issue.",
        ValueError: "Data issue.",
        requests.exceptions.RequestException: "Unexpected request error."
    }

    error_message = error_messages.get(type(e), f"Unexpected error: {e}")
    logging.error(f"{context} {error_message}")
    return error_message


def timer_elapsed(func):   # Для замірювання часу виконання ф-ції func
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'Time elapsed in {func.__name__}: {end_time - start_time:.2f} seconds')
        return result
    return wrapper

# ------------- Parsing logic ---------------------------------
def fetch_content(url, timeout=20, return_soup=True):
    response = requests.get(url, timeout=20)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    html = response.text
    return BeautifulSoup(html, 'html.parser') if return_soup else html


def get_dict_all_categories(url):
    # response = requests.get(url, timeout=20)
    # response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    # soup = BeautifulSoup(response.text, 'html.parser')
    soup = fetch_content(url, timeout=20, return_soup=True)
    # print(f'soup.prettify == {soup.find('ul', class_='menu-categories ng-star-inserted').prettify()}')
    print(f'soup.prettify == {soup.find('ul', class_='menu-categories ng-star-inserted')}')

    dict_all_categories = {}
    # list_tags_a = soup.find('ul', class_='menu-categories ng-star-inserted').find_all('a', class_='menu-categories__link')
    list_tags_a = soup.find_all('a', class_='ssr-menu-categories__link')

    for tag in list_tags_a:
        href = tag.get('href')  # за відсутності атрибуту 'href', поверне None замість помилки
        text = tag.get_text(strip=True)
        if href and text:  # якщо атрибути не порожні; Щоб уникнути додавання порожніх ключів або значень до словника.
            dict_all_categories[href] = text
    return dict_all_categories


@lru_cache(maxsize = 3000)  # Для кешування повторних URL адрес
def fetch_url_with_retries(url, retries=3, timeout=10):
    """
    Fetches a URL with a specified number of retries on network-related errors.  #  Fetches the HTML content of a webpage with error handling for network issues.

    Args:
        url (str): The URL of the webpage to fetch.
        retries (int): Number of retry attempts.
        timeout (int): Timeout in seconds for the request.

    Returns:
        str: The HTML content of the page, or an error message if an exception occurs.
    """
    
    if not is_connected():  # Якщо нема інтернет-зв'язку
        return 'Error: No internet connection'

    # Повтори при таймаутах
    for attempt in range(retries):
        try:
            print(f'Fetching URL: {url}')  # !!! переконайтеся, що ви дійсно отримуєте нову сторінку
            
            # response = requests.get(url, timeout=timeout)
            # response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            # html = response.text
            html = fetch_content(url, timeout=10, return_soup=False)
            
            if html is None or len(html.strip()) == 0:
                return []
            
            return html  # Успішний запит, - Повертаємо контент
        
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}.")
            if attempt == retries - 1:  # Last attempt
                return handle_exception(e, context=f"Fetching URL {url}")
            time.sleep(2 ** attempt)  #  Покрокове збільшення затримки, - задля уникнення блокування сервером

    return 'Error: Failed to fetch the URL after multiple retries.'  # Якщо усі спроби були невдалі:...


def extract_element(soup, tag, class_name):  # def get_item_any_way(soup, tag, class_name):
    """
    Повертає текст елемента або порожній рядок, якщо елемент не знайдено
    """
    element = soup.find(tag, class_=class_name)
    return element.get_text(strip=True) if element else ''


def get_round(price):
    if len(price) >= 5:
        return float(price[:-4])
    else:
        return price


def trim_ratio(ratio):
    if ratio[0] == '/':
        ratio = ratio[1:]
    return ratio


def trim_volume(volume):
    volume = volume.replace(',', '.')
    if len(volume) >= 1:
        return eval(volume)
    else:
        return volume


def get_ratio_and_volume(volume):
    """
    Виокремлюємо з текст. змінної volume нові дві змінні:
        ratio_part (text; міра обсягу)
    та
        volume_part (float; розмір обсягу)
    """
    if len(volume) >= 1:
        pos_last_num = len(volume)
        for index, symbol in enumerate(reversed(volume)):
            if symbol.isdigit():
                pos_last_num = len(volume) - index
                break
        # if pos_last_num == len(volume) and not pos_last_num[0].isdigit():
        if pos_last_num == len(volume) and volume[0].isalpha():
            pos_last_num = 0
        # print(f'index == {index}')
        # print(f'pos_last_num == {pos_last_num}')
        ratio_part = trim_ratio( volume[pos_last_num:] )
        volume_part = trim_volume( volume[:pos_last_num] )
        return ratio_part, volume_part
    else:
        ratio_part, volume_part = '', ''
        return ratio_part, volume_part


def converting_volume_measure(volume_part, ratio_part):
    """
    Зводимо усі ratio_part до дрібніших мір (г та мл) з відповідним обчисленням для volume_part
    """
    # Словник з коефіцієнтами конвертації до базових одиниць
    dict_conversation_factors = {
        'кг': ('г', 1000),
        # 'мл': ('мл', 1),
        'л': ('мл', 1000)
    }

    # for unit, (base_unit, factor) in dict_conversation_factors.items():
    #     if unit in ratio_part:
    #         ratio_part = ratio_part.replace(unit, base_unit)
    #         volume_part *= factor
    #         # print(f'Inside def converting_volume_measure:\nratio_part == {ratio_part}\nvolume_part == {volume_part}')
    #         break   # Припинити після першої знайденої відповідности

    # return int(volume_part), ratio_part

    if isinstance(volume_part, (int, float)) and len(ratio_part) > 0:
        for unit, (base_unit, factor) in dict_conversation_factors.items():
            if 'мл' in ratio_part:
                return int(volume_part), ratio_part
            elif unit in ratio_part:
                ratio_part = ratio_part.replace(unit, base_unit)
                volume_part *= factor
                # print(f'Inside def converting_volume_measure:\nratio_part == {ratio_part}\nvolume_part == {volume_part}')
                # break   # Припинити після першої знайденої відповідности
                return int(volume_part), ratio_part
    # else:
    #     return volume_part, ratio_part
    return volume_part, ratio_part  # тут повертає також і "2.0 г/уп", "2.0 г/шт"

    # Старий неоптимізований код:
    # if 'кг' in ratio_part:
    #     ratio_part = ratio_part.replace('кг', 'г')
    #     volume_part *= 1000
    # if ('л' in ratio_part) and not ('мл' in ratio_part):
    #     ratio_part = ratio_part.replace('л', 'мл')
    #     volume_part *= 1000
    # return int(volume_part), ratio_part


def get_id_tovar(url_card):
    return str( hash( 'silpo.ua' + url_card[10:] ) % 10 ** 8 )   # обтинає хеш до 8-ми цифр


def get_real_discount(current_price, old_price):
    if isinstance(current_price, (int, float)) and isinstance(old_price, (int, float)):
        return int(((old_price - current_price) / old_price) * 100)


def get_price_per_weight(current_price, volume_part, ratio_part):
    # if isinstance(current_price, (int, float)) and isinstance(volume_part, (int, float)) and 'шт' not in ratio_part and 'уп' not in ratio_part: # ratio_part.find('шт') < 0 and ratio_part.find('уп') < 0:
    if isinstance(current_price, (int, float)) and isinstance(volume_part, (int, float)) and ('г' in ratio_part or 'мл' in ratio_part):
    # and all(item not in ratio_part for item in  ['шт', 'кг', 'л', 'уп'] ):
        # Якщо current_price та volume_part - числа, а рядок ratio_part не містить 'шт' / 'уп', тоді:
        # price_per_weight = round( 1000 * ( current_price / float(volume_part) ), 2 )
        return round( 1000 * ( current_price / float(volume_part) ), 2 )
    else:
        return ''


# @timer_elapsed
def parse_product_card(html_card):
    # Extract Data from a Single Product Card
    # Саме в цій функції ми визначаємо усі ті дані, які хочемо дістати з кожної товарної картки
    time.sleep(0.2)
    soup = BeautifulSoup(html_card, 'html.parser')

    current_price = extract_element(soup, "div", "ft-whitespace-nowrap ft-text-22 ft-font-bold")
    current_price = get_round(current_price)

    old_price = extract_element(soup, "div", "ft-line-through ft-text-black-87 ft-typo-14-regular xl:ft-typo")
    old_price = get_round(old_price)

    volume = extract_element(soup, "div", "ft-typo-14-semibold xl:ft-typo-16-semibold")
    ratio_part, volume_part = get_ratio_and_volume(volume)
    # ratio_part = <"шт" / "кг" / "л">
    # volume_part = <1, 0.5, 125>

    discount = extract_element(soup, "div", "product-card-price__sale")
    # if discount != '':
    if len(discount) >= 3:
        discount = int(discount[2:-1])
        real_discount = get_real_discount(current_price, old_price)
        differ_discounts = real_discount - discount
    else:
        differ_discounts = ''

    # print(f'volume_part == {volume_part}')
    # print(f'ratio_part == {ratio_part}')
    volume_part, ratio_part = converting_volume_measure(volume_part, ratio_part)

    price_per_weight = get_price_per_weight(current_price, volume_part, ratio_part)

    title = extract_element(soup, "div", "product-card__title")
    
    try:
        url_card = soup.find("a")["href"] if soup.find("a") else ''
        id_tovar = get_id_tovar(url_card)

        # print(f'url_card == {url_card}')
        subgroup = url_card.split('/')[2].split('-')[0]
    except requests.RequestException as e:
            logging.error(f"Attempt failed for {url_card}.")
            print(f'\nInside Except:\nurl_card == {url_card}\n')
            return handle_exception(e, context=f"Fetching URL {url_card}")

    return {  # for Silpo
        "id_tovar": id_tovar,
        "price_per_weight": price_per_weight,
        "subgroup": subgroup,
        "url_card": url_card,
        "current_price": current_price,
        "old_price": old_price,
        "volume_part": volume_part,
        "ratio_part": ratio_part,
        "discount": discount,
        "real_discount": real_discount,
        "differ_discounts": differ_discounts,
        "title": title,
        "rating": extract_element(soup,
                                         "span",
                                         "catalog-card-rating--value")
    }
        

# @timer_elapsed
def parse_page(html_page):
    # Extract All Product Cards on a Page
    # Parse all cards in a container.
    
    products = {}
    
    soup = BeautifulSoup(html_page, 'html.parser')
    product_cards = soup.find_all('div', class_="products-list__item")  # for Silpo
    
    set_ids = set()
    # Саме тут слід прописати перевірку на унікальність доданих ID кожної картки
    # products = [parse_product_card(str(card)) for card in product_cards if parse_product_card(str(card))['id_tovar'] not in set_ids]
    for card in product_cards:
        current_card = parse_product_card(str(card))
        if current_card['id_tovar'] not in set_ids:
            # Винесемо id_tovar зі словника:
            tmp_id_tovar = current_card['id_tovar']
            del current_card['id_tovar']
            products[tmp_id_tovar] = current_card
            # print(f'current_card == {current_card}')
            # print(f'products == {products}')
            set_ids.add( tmp_id_tovar )
    
    if not products or "Товари закінчилися" in html_page:   # Перевірка на порожній список або помилковий номер сторінки
        return []
    
    return products


def get_max_pagination(base_url):
    # """
    # Повертає найбільшу к-сть сторінок певної категорії
    # """
    # response = requests.get(base_url, timeout=10)
    # response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    # soup = BeautifulSoup(response.text, 'html.parser')
    soup = fetch_content(base_url, timeout=10, return_soup=True)
    return int(soup.find('div', class_='pagination__gutter').find_next_sibling('a').get_text(strip=True))
    

@timer_elapsed
@lru_cache(maxsize = None)
def fetch_all_pages(base_url, start_page=1):
    # Iterate Through Pages
    # Add logic to parse multiple pages using pagination
    # Отримує дані з усіх сторінок категорії
    page_number = start_page
    all_products = []
    previous_url = None    
    # all_pages_data = {}
    dict_entries ={
        'count_entries': 0,
        'sizeof': 0
    }
    # print('Code in fetch_all_pages, Before While Loop')

    # previous_products = None

    max_num_pages = get_max_pagination(base_url) #  Найбільше число у пагінації
    
    while page_number <= max_num_pages:
        url = f"{base_url}?page={page_number}"
        print(f'Fetching URL: {url}')
        # print('Code in fetch_all_pages, In While Loop, Before call fetch_url_with_retries')

        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        final_url = response.url   # URL після редиректу

        # Містить список редиректів. Якщо список не порожній, це означає, що був редирект.
        if response.history:
            print(f"[Redirect history: {[resp.status_code for resp in response.history]}")

        # Перевірка на редирект
        if final_url != url:
            print(f"Redirect detected! Final URL: {final_url}")
            if final_url == previous_url:  # Якщо повернулись до тієї ж сторінки
                print("Rederected to the same page. Stopping.")
                break

        html = fetch_url_with_retries(url, retries=3, timeout=10)

        if not html:
            print("Empty HTML or failed to fetch page.")
            break

        # print('Code in fetch_all_pages, In While Loop, After call fetch_url_with_retries')
        # print('Code in fetch_all_pages, In While Loop, Before call parse_page')
        products = parse_page(html)
        
        url_page_category = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
        # print(f'\n\nproducts == {products}\n\n')
        save_to_file(products, url_page_category.split('/')[4] + '.jsonl')
        # print('Code in fetch_all_pages, In While Loop, After call parse_page')
        dict_entries['count_pages'] = dict_entries.get('count_pages', 0) + 1
        dict_entries['count_entries'] = dict_entries.get('count_entries', 0) + len(products)
        # dict_entries['sizeof'] = dict_entries.get('sizeof', 0) + sys.getsizeof(products)

        # print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\nsizeof = {dict_entries['sizeof']}\n")
        print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\n")
        
        # all_pages_data[f'page_{page_number}'] = products
        # all_products.extend(products)
        all_products.append(products)
        page_number += 1

        previous_url = final_url  # Зберігаємо URL для порівняння у наступному циклі
    # print('Code in fetch_all_pages, After While Loop')

    # print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\nsizeof = {dict_entries['sizeof']}\n")    
    
    # print('The end code in fetch_all_pages (Before Return)')
    return all_products


@timer_elapsed
def save_to_file(data, fname='data.jsonl'):
    # Save data to a file after each page to avoid overloading RAM.
    # Use JSON Lines for incremental saving
    # print('Begin code in save_to_file')
    file_path = get_file_path(fname)
    with file_path.open(mode='a', encoding='utf-8') as file:
        # for record_key, record_value in data.items():
        if type(data) is list:
            for record in data:
                file.write(json.dumps(record) + '\n')
        elif type(data) is dict:
            for record in data.items():
                file.write(json.dumps(record) + '\n')
    # print('The End code in save_to_file')
    

@timer_elapsed
def fetch_all_stores(store_urls):
    # Process Multiple Stores
    # Extend to iterate over multiple base URLs
    all_stores = {}
    for store_id, base_url in store_urls.items():
        all_stores[store_id] = fetch_all_pages(base_url, start_page=1)
    return all_stores


# !!!
# Краще прибрати цей код
# # !!! Рішення з використанням eval() є небезпечним!
# # Які є засоби убезпечити код в таких випадках?..
# def load_data_with_jsonl(fname, str_statement):
#     # Витягає дані, які відповідають певній умові коду str_statement
#     file_path = str(get_file_path(fname))
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return [json.loads(line) for line in f if eval(str_statement)]

# !!! Рішення з використанням eval() є небезпечним!
# Які є засоби убезпечити код в таких випадках?..
def load_data_with_jsonl(fname):
    # Витягає дані, які відповідають певній умові коду str_statement
    
    # file_path = str(get_file_path(fname))
    # with open(file_path, 'r', encoding='utf-8') as f:
    #     # return [json.loads(line) for line in f]
    #     return json.load(f)
    # # Який є швидший спосіб витягти усі записи з файлу?

    file_path = str(get_file_path(fname))
    new_list = []
    # if not file_path.exists():
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found')
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # return json.load(f)
                for line in f:
                    record = json.loads(line)
                    new_list.append(record)
        except json.JSONDecodeError as e:
            raise ValueError(f'Помилка декодування JSON у файлі {file_path}: {e}')
    
    return new_list


def get_top_volume_parts(fname, top_n=10):
    volume_counter = Counter()

    # Перший прохід - обчислення частоти volume_part
    file_path = str(get_file_path(fname))
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                volume_counter[record['volume_part']] += 1
            except (json.JSONDecodeError, KeyError):
                continue

        print(f'volume_counter == {volume_counter}')

    # Топ-N значень volume_part
    top_volumes = [volume for volume, _ in volume_counter.most_common(top_n)]
    return (top_volumes, volume_counter)


# 2) Порівняй ціни на товари з однаковою вагою / назвою підгрупи
def compare_prices(fname):
    # Виведи усі товари вагою 200 г, з назвою 'moloko', з їх цінами та url_card's
    file_path = str(get_file_path(fname))
    list_products = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'moloko':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'maslo':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'yogurt':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'syrok':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'syr':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'vershky':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'napii':
                # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'kefir':
                if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'smetana':
                    list_products.append(record)
                # dict_volume_counter = get_top_volume_parts(fname, top_n=10)[1]
                # if dict_volume_counter[record['volume_part']] == 
            except (json.JSONDecodeError, KeyError):
                continue
    return list_products


def get_sorted_records(fname):
    file_path = str(get_file_path(fname))
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parsed_line = json.loads(line)
                data.append(parsed_line)
        return sorted(data, key=lambda x: [x[1]['price_per_weight'] is None, x[1]['price_per_weight'] == '', x[1]['price_per_weight']], reverse=True)
    # return sorted(data, key=lambda x: float(x[1]['price_per_weight']) if x[1]['price_per_weight'] == '' else, reverse=True)


# def get_sorted_records(fname):
#     # Повертає продукти, які є найдорожчими (за 1 кг / 1 л)    file_path = str(get_file_path(fname))
#     list_of_listts_records = []
#     file_path = str(get_file_path(fname))
#     # with file_path.open(mode='r', encoding='utf-8') as f:
#     with open(file_path, 'r', encoding='utf-8') as f:
#         for line in f:
#             try:
#                 record = json.loads(line)
#                 # print(record)
#                 # print(record['ratio_part'])
#                 if 'ratio_part' in record and ('г' in record['ratio_part'] or 'л' in record['ratio_part']):
#                     list_of_listts_records.append(record)
#                     # print(list_of_listts_records)
#                 # print(f'list_of_listts_records == {list_of_listts_records}')
                
#                 # if record['volume_part'] == 200 and record['url_card'].split('/')[2].split('-')[0] == 'smetana':
#                 #     list_products.append(record)
#                 # # dict_volume_counter = get_top_volume_parts(fname, top_n=10)[1]
#                 # # if dict_volume_counter[record['volume_part']] == 
#             except (json.JSONDecodeError, KeyError):
#                 continue
    
#     # dict_sorted_records = sorted(records, key = lambda x: x.get('price_per_weight', 0), reverse=True)
    
#     # dict_sorted_records = sorted(records, key = lambda x: getattr(x, 'price_per_weight'), reverse=True)
#     # dict_sorted_records = sorted(records, key = lambda x: getattr(x, 'current_price'), reverse=True)
    
#     # dict_sorted_records = sorted(records.items(), key = lambda x: x[1], reverse=True)
#     dict_sorted_records = sorted(records.items(), key = get_val_price_per_weight, reverse=True)
#     return dict_sorted_records
#     # return records

# #     dict_sorted_records = sorted(records.items(), key = get_val_price_per_weight, reverse=True)
# #                                  ^^^^^^^^^^^^^
# # AttributeError: 'list' object has no attribute 'items'



def get_val_price_per_weight(item):
    price_per_weight = item[1].get("price_per_weight", 0)
    return price_per_weight


@timer_elapsed
def main():
    logging.basicConfig(
        filename=get_file_path('parser_errors.log'),
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode = 'a'   # Дозаписування нових записів до файлу
    )
    
    # Prototype First Point
    # Start with a single product card
    # url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234?page=1'
    # html = fetch_url_with_retries(url, retries=3, timeout=10)
    # product = parse_page(html)
    # print(product[0])  # View the first product card


    # # Expanding Gradually
    # # Pass the URL of the next store as an argument to fetch_all_pages
    
    base_url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
    fname = 'molochni-produkty-ta-iaitsia-234.jsonl'
    
    file_path = str(get_file_path(fname))
    # if not os.path.isfile(file_path):   # якщо файлу ще нема, тоді створімо його:
    #     all_products = fetch_all_pages(base_url, start_page=1)

    # list_data = load_data_with_jsonl(file_path)
    # print(f'list_data[0] == {list_data[1]}')

    # top_volumes_freq = get_top_volume_parts(fname, top_n=10)
    # print(f'top_volumes_freq == {top_volumes_freq[:10]}')
    #     # volume_counter == Counter({200: 176, 180: 150, 300: 148, 100: 121, 400: 102, 350: 97, 500: 97, 1: 97, 900: 91, 250: 86})
    #     # Як бачимо, більшість товарів мають пакування у 100..500 г

    # list_prods = compare_prices(fname)
    # print(f'list_prods == {list_prods}')


    # fname = 'molochni-produkty-ta-iaitsia-234.jsonl'
    dict_sorted_products = get_sorted_records(fname)

    file_name = 'sorted_' + fname
    save_to_file(dict_sorted_products, file_name)


    # list_of_dicts = {908058: {"url_card": "/product/maslo-solodkovershkove-molokiia-73-908058", "current_price": 69.99, "old_price": 99.0, "ratio_part": "\u0433", "volume_part": 180, "price_per_weight": 388.83, "title": "\u041c\u0430\u0441\u043b\u043e \u0441\u043e\u043b\u043e\u0434\u043a\u043e\u0432\u0435\u0440\u0448\u043a\u043e\u0432\u0435 \u00ab\u041c\u043e\u043b\u043e\u043a\u0456\u044f\u00bb 73%", "discount": "29", "rating": "4.5"},
    #                 28734: {"url_card": "/product/moloko-selianske-pytne-ultrapasteryzovane-2-5-28734", "current_price": 34.99, "old_price": 48.19, "ratio_part": "\u0433", "volume_part": 900, "price_per_weight": 38.88, "title": "\u041c\u043e\u043b\u043e\u043a\u043e \u00ab\u0421\u0435\u043b\u044f\u043d\u0441\u044c\u043a\u0435\u00bb \u043f\u0438\u0442\u043d\u0435 \u0443\u043b\u044c\u0442\u0440\u0430\u043f\u0430\u0441\u0442\u0435\u0440\u0438\u0437\u043e\u0432\u0430\u043d\u0435 2,5%", "discount": "27", "rating": "4.9"},
    #                 947496: {"url_card": "/product/yogurt-delissimo-fantasia-z-kulkamy-zlakovymy-v-shokoladnii-glazuri-6-3-947496", "current_price": 27.99, "old_price": 34.99, "ratio_part": "\u0433", "volume_part": 100, "price_per_weight": 279.9, "title": "\u0419\u043e\u0433\u0443\u0440\u0442 \u0414\u0435\u043b\u0456\u0441\u0441\u0456\u043c\u043e Fantasia \u0437 \u043a\u0443\u043b\u044c\u043a\u0430\u043c\u0438 \u0437\u043b\u0430\u043a\u043e\u0432\u0438\u043c\u0438 \u0432 \u0448\u043e\u043a\u043e\u043b\u0430\u0434\u043d\u0456\u0439 \u0433\u043b\u0430\u0437\u0443\u0440\u0456 6,3%", "discount": "20", "rating": ""},
    #                 799508: {"url_card": "/product/moloko-ultrapasteryzovane-premiia-2-5-799508", "current_price": 46.99, "old_price": "", "ratio_part": "\u0433", "volume_part": 900, "price_per_weight": 52.21, "title": "\u041c\u043e\u043b\u043e\u043a\u043e \u0443\u043b\u044c\u0442\u0440\u0430\u043f\u0430\u0441\u0442\u0435\u0440\u0438\u0437\u043e\u0432\u0430\u043d\u0435 \u00ab\u041f\u0440\u0435\u043c\u0456\u044f\u00bb\u00ae 2,5%", "discount": "", "rating": "4.2"},
    #                 939585: {"url_card": "/product/yogurt-molokiia-bilyi-gustyi-3-939585", "current_price": 83.99, "old_price": 129.0, "ratio_part": "\u0433", "volume_part": 1000, "price_per_weight": 83.99, "title": "\u0419\u043e\u0433\u0443\u0440\u0442 \u041c\u043e\u043b\u043e\u043a\u0456\u044f \u0431\u0456\u043b\u0438\u0439 \u0433\u0443\u0441\u0442\u0438\u0439 3%", "discount": "35", "rating": ""}}
    
    # # list_of_dicts = [{"id_tovar": "908058", "url_card": "/product/maslo-solodkovershkove-molokiia-73-908058", "current_price": 69.99, "old_price": 99.0, "ratio_part": "\u0433", "volume_part": 180, "price_per_weight": 388.83, "title": "\u041c\u0430\u0441\u043b\u043e \u0441\u043e\u043b\u043e\u0434\u043a\u043e\u0432\u0435\u0440\u0448\u043a\u043e\u0432\u0435 \u00ab\u041c\u043e\u043b\u043e\u043a\u0456\u044f\u00bb 73%", "discount": "29", "rating": "4.5"},
    # #                 {"id_tovar": "28734", "url_card": "/product/moloko-selianske-pytne-ultrapasteryzovane-2-5-28734", "current_price": 34.99, "old_price": 48.19, "ratio_part": "\u0433", "volume_part": 900, "price_per_weight": 38.88, "title": "\u041c\u043e\u043b\u043e\u043a\u043e \u00ab\u0421\u0435\u043b\u044f\u043d\u0441\u044c\u043a\u0435\u00bb \u043f\u0438\u0442\u043d\u0435 \u0443\u043b\u044c\u0442\u0440\u0430\u043f\u0430\u0441\u0442\u0435\u0440\u0438\u0437\u043e\u0432\u0430\u043d\u0435 2,5%", "discount": "27", "rating": "4.9"},
    # #                 {"id_tovar": "947496", "url_card": "/product/yogurt-delissimo-fantasia-z-kulkamy-zlakovymy-v-shokoladnii-glazuri-6-3-947496", "current_price": 27.99, "old_price": 34.99, "ratio_part": "\u0433", "volume_part": 100, "price_per_weight": 279.9, "title": "\u0419\u043e\u0433\u0443\u0440\u0442 \u0414\u0435\u043b\u0456\u0441\u0441\u0456\u043c\u043e Fantasia \u0437 \u043a\u0443\u043b\u044c\u043a\u0430\u043c\u0438 \u0437\u043b\u0430\u043a\u043e\u0432\u0438\u043c\u0438 \u0432 \u0448\u043e\u043a\u043e\u043b\u0430\u0434\u043d\u0456\u0439 \u0433\u043b\u0430\u0437\u0443\u0440\u0456 6,3%", "discount": "20", "rating": ""},
    # #                 {"id_tovar": "799508", "url_card": "/product/moloko-ultrapasteryzovane-premiia-2-5-799508", "current_price": 46.99, "old_price": "", "ratio_part": "\u0433", "volume_part": 900, "price_per_weight": 52.21, "title": "\u041c\u043e\u043b\u043e\u043a\u043e \u0443\u043b\u044c\u0442\u0440\u0430\u043f\u0430\u0441\u0442\u0435\u0440\u0438\u0437\u043e\u0432\u0430\u043d\u0435 \u00ab\u041f\u0440\u0435\u043c\u0456\u044f\u00bb\u00ae 2,5%", "discount": "", "rating": "4.2"},
    # #                 {"id_tovar": "939585", "url_card": "/product/yogurt-molokiia-bilyi-gustyi-3-939585", "current_price": 83.99, "old_price": 129.0, "ratio_part": "\u0433", "volume_part": 1000, "price_per_weight": 83.99, "title": "\u0419\u043e\u0433\u0443\u0440\u0442 \u041c\u043e\u043b\u043e\u043a\u0456\u044f \u0431\u0456\u043b\u0438\u0439 \u0433\u0443\u0441\u0442\u0438\u0439 3%", "discount": "35", "rating": ""}]

    # print(sorted(list_of_dicts.items(), key = get_val_price_per_weight, reverse=True))
    #     #  price_per_weight = item[1].get("price_per_weight", 0)
    #     #                    ~~~~^^^
    #     # KeyError: 1


    # print(f'{top_volumes_freq.__name__} == {top_volumes_freq}')
    # print(f'len == {len(list_data)}\nlist_data == {list_data}')
    # common_val = Counter(list_data.values()).most_common
    # print(f'common_val == {common_val}')


    # print(f'num = {get_max_pagination(base_url)}')
    # #  Найбільше число у пагінації

    # print('Дані зібрано')
    # # save_to_file(all_products, 'data.jsonl')
    # print('Дані збережено до файлу "data.jsonl"')


    # # url = 'https://silpo.ua'
    # url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234?page=1'
    # # dict_all_categories = get_dict_all_categories(url)
    # # print(f'categories = {dict_all_categories}')


    # soup = fetch_content(url, timeout=20, return_soup=True)
    # # print(f'soup.prettify == {soup.find('ul', class_='menu-categories ng-star-inserted').prettify()}')
    # # print(f'soup.prettify == {soup.find('ul', class_='menu-categories ng-star-inserted')}')
    
    # list_tags_a = soup.find('div', class_='container').find_all('a')
    # # list_tags_a = soup.find_all('a')
    # print(f'size(list_tags_a) == {len(list_tags_a)}')
    # for tag_a in list_tags_a:
    #     print(f'\ntag_a.get_text(strip=True) == {tag_a.get_text(strip=True)}')
    #     print(f"tag_a.get('href') == {tag_a.get('href')}")
    #     print(f'tag_a == {tag_a}\n')


    # dict_all_categories = {}
    # # list_tags_a = soup.find('ul', class_='menu-categories ng-star-inserted').find_all('a', class_='menu-categories__link')
    # list_tags_a = soup.find_all('a')
    # print(f'list_tags_a:\n{list_tags_a}')

    # current_price = "64.99 \u0433\u0440\u043d"
    # current_price = ""
    # print(get_round(current_price))

    # volume = "10*10г/уп"
    # ratio, volume = get_ratio_and_volume(volume)
    # print(f'volume == {volume}')
    # print(f'ratio == {ratio}')
    # # print(get_ratio_and_volume(volume))

    # discount = "- 34%"
    # discount = discount[2:-1]
    # print(f"discount == {discount}")

    # discount = "- 6%"
    # discount = discount[2:-1]
    # print(f"discount == {discount}")

    # # volume = '90*23'
    # volume = 'шт'
    # volume = volume.replace(',', '.')
    # print(f'volume == {volume}')
    # # volume_part = trim_volume(volume)
    # volume_part = eval(volume)
    # print(f'volume_part == {volume_part}')

    # ratio = 'шт'
    # ratio_part = trim_ratio(ratio)
    # print(f'ratio_part == {ratio_part}')
    
    # my_list_ids = [908058,28734,947496,799508,939585,936492,836239,871982,975715,903568,862307,862308,782890,799507,836238,949953,954310,815587,728713,912383,960334,836196,903565,830217,890483,868167,936491,929054,960494,954311,947495,961300,924819,655611,859908,736353,837453,851859,746443,926688,949441,951079,926686,736354,746454,907210,746451,957358,957359,960332,968472,949438,949443,949442,949436,926685,926687,914984,968473,968471,960333,972846,951610,746445,883228,871808,871809,879589,811186,728714,436418,436420,181642,452276,892643,716079,646104,874616,829005,745825,69262,933071,830218,866829,842271,872537,746913,842283,932238,872176,682859,928712,906990,838497,878789,846754,945720,928145,839326,633700,812568,913405,954288,954286,837449,917296,908737,908738,705767,809640,874615,587355,910653,935468,919637,819149,819150,746914,808149,839328,947494,830225,709896,837452,878542,947879,944800,920810,962255,892644,838498,837450,815590,871874,906988,778675,640116,215612,441882,926040,802294,820341,758546,821846,871875,966826,215607,916055,928141,931725,647808,576829,383229,676328,856423,709900,935095,935096,935133,928144,961704,555471,329025,555470,547004,935092,914585,913220,839325,802382,863535,931724,215615,935148,937686,910658,950417,863534,836541,839545,584788,650794,968998,961705,917589,913056,935139,935091,949578,928143,914623,795320,709895,873839,885638,911503,605304,963083,918566,915548,928140,947909,935141,70262,950418,941572,966822,913221,913055,961706,758191,752728,912614,857555,767872,691798,863526,711180,935151,951591,947483,937687,435227,547132,942733,954289,966821,925145,914582,848613,914622,953424,840582,724312,782887,836079,690796,811977,820340,819148,880828,583255,953423,960335,917293,913222,928142,944564,929058,186381,375698,947880,942730,954287,966731,941571,917299,815589,957116,775006,560380,649036,823885,709899,702510,690795,647794,739879,837451,740859,775007,815585,830216,865983,904546,866587,916970,913572,925144,963078,968994,928704,375695,456680,28205,933067,942635,937688,949925,950419,968611,967775,935135,909235,913406,913047,915547,968992,968440,779342,709893,666091,547009,488639,875443,913576,857478,836540,842282,847787,854265,823122,876400,875045,875056,808148,744351,752723,815591,720126,705768,709897,709898,823883,815586,848612,845009,913575,913578,894502,894503,584783,584246,666106,737704,957117,951585,951611,973555,923745,917218,915546,914584,914291,935150,939925,941244,940574,931726,935319,967865,966732,966730,968996,960336,941573,519445,95513,186388,933069,947911,942357,944563,941574,942359,949584,938204,955450,950473,935093,925136,925137,938203,947910,937693,923050,912613,914182,914285,923051,972125,953866,951584,953340,885630,913057,885635,803705,827092,720133,739119,844101,752722,870751,862237,674753,875054,863538,846426,758549,838496,702509,833420,863642,842303,846423,875041,507382,584785,584247,641880,729196,720129,647784,786252,953422,955452,913054,913573,913574,914719,925139,937691,926044,932921,933521,935152,954303,944371,942633,944372,949116,934597,952766,937689,945696,390554,318549,408658,390553,527083,558939,440574,355212,82447,82983,28735,389642,204071,931579,925621,946534,946351,935149,944572,928703,925135,942658,949118,925140,938360,959540,960451,774672,612305,737602,719167,711179,666088,585867,573507,599823,576688,891134,878541,910650,861921,865848,800237,821845,719166,815576,870750,854430,751012,690797,614112,711182,791895,875164,875048,774677,784579,851781,751010,846425,843108,848614,840585,647803,692625,885627,866584,871984,839327,846405,905468,875166,843108,848614,840585,647803,692625,885627,866584,871984,839327,846405,905468,875166,875167,893596,880464,892639,584407,609903,650808,566112,558941,548446,536280,763700,745431,599195,777178,777587,960626,959541,973559,951594,951603,953867,966825,967486,973562,919396,919397,857479,917588,914288,910655,910657,941886,929119,935820,935134,935153,935320,933123,966824,960448,946353,941246,949577,917297,944374,950469,941247,941430,942634,937690,938191,942732,945958,947486,947487,947913,928138,503775,33530,50618,33529,255332,263285,63259,539325,505651,255333,424674,929458,932232,930417,930418,933518,933124,926039,946350,939258,940380,937004,953344,935147,949440,950470,944573,944565,944799,955451,957188,957229,963052,935094,931675,922122,925138,941887,909236,909237,910654,909877,909878,913104,914289,914290,869921,851780,842279,917749,881294,972958,951612,974966,952765,974829,973557,975028,795319,798036,605295,607301,609883,720273,716286,745208,752726,752383,680698,677647,541678,644338,655902,597518,584782,576687,891135,890843,881291,875059,891133,913108,909104,909882,885625,857553,866586,881290,800238,811978,674752,824909,724311,840586,832879,843894,844102,844103,844104,752724,753176,863540,853126,774676,784584,745430,875047,875055,875046,784583,720207,704727,794122,777149,851783,857541,863530,751009,751001,846761,759800,759801,815575,812531,720125,713792,720208,720274,677183,662492,658046,655890,655891,691396,832877,827093,823936,816398,863643,871983,844116,885626,911628,905470,914279,913101,913099,890845,894505,643814,655889,536257,584230,519444,322663,619480,609886,541679,548448,666107,666108,666089,662354,752727,751004,745206,612304,646105,960449,960450,959530,959682,973297,973298,951586,954744,954745,957252,972023,972025,972642,973560,973561,960958,960411,960085,956124,921088,921089,917587,914286,832878,915718,913106,909887,910656,913098,921095,941442,940381,923366,923364,929118,929839,921085,931676,931677,933070,933522,963053,963054,969938,969940,959543,960337,949580,949587,954746,954304,953863,946538,946220,946352,943009,944801,916971,944113,949585,949006,949117,935140,935464,935466,935467,935758,953345,941248,941441,941432,937664,938205,938206,939926,937697,939252,942014,944562,947912,930592,929457,381862,528229,543964,467449,482002,536275,929456,929951,930528,933517,933519,933520,946535,933068,927659,946533,946241,944853,944854,944855,942631,942330,937696,937740,942000,942077,942358,942636,941433,941575,941431,951604,934596,953343,935465,949582,951587,951588,951589,939257,946536,946537,954747,950414,950415,960172,959544,959545,959091,957253,950474,972011,968610,969939,969573,964265,964266,963055,935987,931223,931224,931225,921743,921744,921086,921084,929838,937741,949439,949581,924996,938192,940382,939254,939256,941570,941443,941728,923365,941434,939253,937005,932242,931674,905314,909885,913052,911481,909886,913105,913103,915543,915544,915545,853125,914280,915549,915716,915717,922123,920813,920814,959734,969937,970948,969285,974980,972022,959546,960173,976158,976626,972024,951595,976159,976545,976546,976627,976972,974830,969935,969936,969508,969284,963443,955009,955053,956306,955453,956566,951602,953339,953341,957118,958061,959683,959699,959681,960174,960175,961947,961413,960084,960893,975439,975035,792086,771997,766733,800239,597464,605303,726270,719169,719170,716285,745205,691399,662353,541251,658045,894504,890844,879212,875042,875442,913100,911748,905315,905316,914278,905469,905471,907568,909883,909884,910651,885634,845011,844100,863585,856172,869920,873803,863644,795515,808190,808191,812530,832876,830219,836195,715940,716080,716081,716082,711100,691397,691398,689409,666110,658047,808187,720202,812532,812533,812534,814596,815182,815183,819946,815692,815693,728673,728674,842280,845012,846424,751002,751043,755012,863539,856170,851782,774675,872922,872923,623245,792087,812535,856171,878540,35406,60076,69532,72568,74065,435223,524523,533172,547027,566113,580623,583023,597466,598065,605305,606908,606909,606910,606911,606912,606913,609905,648548,655612,657690,658795,658797,662351,669303,669304,690890,699993,699994,703244,702511,702977,702981,702982,702983,702984,708020,708021,709777,711181,716852,716863,719171,737776,742710,745207,745210,745503,745504,744676,744979,748398,746444,746446,746447,746448,746449,746450,746452,746455,746459,746460,766726,766729,766732,758626,767771,765216,777586,777701,784575,784577,784582,785544,786267,789887,803706,803898,811687,815180,815181,815588,823155,823918,836214,838947,838948,840580,840581,841031,847781,847782,847783,847784,847785,845782,845783,845784,853127,856619,856068,856069,857563,859171,861920,863690,865980,865982,866272,866585,871876,872924,872925,872926,875057,875165,881122,879024,879590,884475,885624,889153,889155,890624,890842,890846,892729,892730,892506,905631,905313,906989,908386,908387,908388,908389,909880,909881,868166,905473,706815,637646,568754,912615,895019,915550,915551,915552,732470,915783,916415,677184,917312,917313,884477,913988,839623,917095,919995,720128,776160,919398,135299,248689,328777,328780,328783,536046,536938,658555,663470,731380,745281,745282,745283,748399,750678,758140,769428,770940,770941,770942,770943,770944,770945,770946,770949,774133,774134,774135,774136,786723,790535,790536,790537,797968,811213,811214,811215,820379,820380,820381,824290,840785,840786,874775,881282,881788,883022,883983,886898,888888,888890,888892,888893,889278,889280,892747,892748,892750,892751,544050,602373,602375,641970,721122,721123,723149,723152,736121,811184,839046,877706,877708,877709,877710,877712,877713,877715,877716,877717,891340,163849,658799,810897,834402,911482,911484,911485,912608,912609,912610,917383,917384,917385,917386,917387,917388,917389,917595,917596,919665,921087,921090,921740,724848,878723,901406,904156,905250,905251,905253,905254,905476,912611,912612,921704,745435,685914,685916,718669,893617,916865,88432,344520,348408,458862,487462,487466,544442,669938,669939,671600,676586,893912,917932,923937,923939,923938,924859,925141,925143,925311,925312,926038,926364,927298,912401,929120,904413,752719,927658,930857,930859,930858,930860,932240,931523,932239,932241,910666,933110,933111,935145,935146,935321,935157,936206,931397,930538,937698,937789,910670,910671,910672,910674,938193,938330,938328,938329,938331,940383,940384,940385,910665,940596,941243,941245,941597,942630,942632,923367,923368,941999,945962,947067,947068,947072,944561,949487,949486,949579,949583,949586,950373,950374,950476,950477,950383,950416,951590,951592,953342,953864,953296,953652,954302,954306,954305,954309,955008,944933,944938,944934,944936,948590,948591,956335,956334,957106,957105,957108,957107,957109,957110,957111,957112,957113,957115,957114,958054,958058,958062,958064,958056,958055,958053,958059,958057,958060,958063,958065,959092,959230,959090,959467,959532,959531,949938,959483,959679,959698,959892,961329,960896,960447,946833,961301,961302,961974,961972,962101,962102,894520,894523,894521,962738,963082,963081,927350,963047,961441,961443,961442,961440,969568,970950,970951,970949,961989,949992,949991,969206,972046,972044,972045,973296,976472,976628,527043,377537,935136,935143,935836,925074,937694,842981,808035,918499,895667,923970,959697,755249,690892,656772,893729,907249,907250,790501,808034,808041,709889,655898,676823,808038,716715,844051,680615,785001,873801,889157,680614,680616,7924,33534,62589,64519,83653,103180,180494,192546,232263,331488,360027,365269,366477,400624,417931,417945,447579,463580,465469,465470,466551,467454,467457,475707,480608,501517,502441,509166,514527,514530,527050,527055,540538,540796,541677,547028,558942,569563,569571,569645,573503,573513,575400,576679,576680,576681,576682,578059,587160,590661,597465,610841,612843,612845,620944,620945,655892,655897,655899,662352,663049,676821,677646,677831,697564,698352,698353,704345,705215,705675,708032,708034,712027,716406,720114,720210,721217,723158,723159,727695,735157,735158,735159,735160,737777,737778,737779,746453,746456,746457,746458,750883,750884,751005,751006,751007,751042,774148,774674,778087,778088,774678,774681,778089,778090,778091,766476,778676,766728,757781,757792,767727,763773,765215,770645,771995,771996,777584,782787,784573,784574,784586,785000,786251,786372,788235,790500,791896,791897,792085,792117,793005,794121,795321,794333,794334,794335,799788,800232,800234,800243,800244,799419,800378,800379,802286,803702,803703,803704,803707,803891,803892,806766,808188,808189,815577,815582,815584,820142,823153,823846,823870,823884,823941,825702,829000,830220,830221,830222,833063,833064,833065,833066,832120,836078,836175,836176,836177,836205,836206,836207,836208,836209,836210,837379,837380,837381,838935,842091,842092,842273,842274,842275,842278,842281,842306,842307,840663,841026,841028,843888,843889,846763,844115,844117,844220,844221,844222,845000,845001,845002,845010,848443,848444,848445,848446,848447,850555,850728,852602,837382,837407,837446,837447,837448,838493,838494,838495,854428,856424,856621,854041,857557,857658,857659,857660,859622,859624,859674,861590,861922,861923,861924,862215,862304,862306,863691,863527,863528,863529,863536,865981,865984,866164,866820,867709,871988,871877,870752,870753,873802,873838,872536,875444,875044,875058,876788,878788,879200,879201,879202,879203,879204,879586,879588,880825,880826,880827,884476,887729,888147,885628,885629,885631,885633,885639,885642,885643,885695,885696,885697,885698,885699,883084,883085,883086,883087,890482,889154,889156,889158,889159,887121,890580,890588,892779,893730,893731,893732,893948,893949,894506,894507,894508,894509,894510,895683,901211,903566,903567,907248,908040,908041,908808,908809,908810,908811,908812,909103,909238,909879,879587,775017,477816,567021,540815,911746,911747,844052,861925,782786,888148,773653,912174,912175,912176,411528,912589,846762,912590,854431,854432,854433,885694,913048,913049,913050,913051,913058,913102,913107,863537,914985,914583,914586,914587,914588,914589,914590,892909,892911,863583,863581,863584,467450,377543,502647,806764,541249,912378,912381,912379,912380,916450,892910,917037,917038,917039,917040,916972,89074,89076,134379,917295,830794,830795,830796,830797,556128,556129,892908,913577,918497,918562,918563,918564,918565,537715,913193,863676,863677,863679,890660,583256,863582,863578,863579,863580,920811,4931,417935,418544,426776,439713,458165,487104,534367,536482,541250,548447,549207,569945,573433,582818,584554,650350,658162,658163,659519,663114,663115,665218,693336,701961,709901,721126,726333,744700,758134,758135,758136,758138,765081,765083,765089,765091,770948,777455,777457,787047,788236,790559,790560,790561,790562,794487,795227,795229,797963,797966,797967,815578,815579,815581,816916,818681,818682,818683,818684,818685,818686,818687,818688,818692,818693,818694,818695,818696,825697,829044,832875,836084,849870,855328,855330,858035,858036,858037,860747,861498,861499,861500,861501,861502,861591,864851,864852,864853,864855,864856,874773,874774,883023,888894,888895,888896,889111,889112,889113,889114,889115,889116,889117,889118,889122,889123,892749,412736,465417,571775,602374,602376,602380,602381,602382,602383,602384,618842,641969,641985,641986,641988,641991,658166,721124,721125,723148,723151,765082,783925,784572,794488,795226,815580,815583,823631,840583,855327,855329,856860,868387,868388,868389,868391,877714,877718,885530,885531,921729,60205,552077,666087,710897,710899,784578,784580,810900,810901,865291,918763,919433,919434,919435,919666,919667,921728,40103,97774,125083,489904,720350,740235,789904,810898,810899,893554,901410,901411,901412,901413,901414,901415,901416,901417,901418,901419,901420,901421,901422,901423,901424,901425,901426,901427,901428,901429,901430,901431,901433,901434,901435,901436,901437,902602,904560,904561,904562,904563,904564,904565,906139,906140,911483,911486,602500,659384,712248,765187,894741,894742,894744,901201,911099,435403,538762,602466,685913,857470,901216,902754,344516,344526,348333,348350,481085,492933,534732,893689,893690,893785,893787,893911,894213,895020,895021,895022,922650,922651,922652,922653,922654,922655,901236,901240,922120,922121,923170,923171,923968,923969,923971,924031,924032,923746,925100,924773,924774,924775,924776,924777,924778,926013,928139,928695,928696,926681,926682,926683,926684,348936,901084,901085,901086,930600,930601,930602,930416,930257,930415,930414,931673,929056,929057,933126,873556,935137,935138,935142,935144,929055,690856,935158,937692,937695,937699,936490,938190,939255,939924,940804,941439,941440,941444,926689,926690,926691,926692,942360,811287,942328,942329,943008,943011,943012,943243,943773,944373,945934,945959,945960,945961,910235,948632,949111,949110,424821,949488,949566,949565,949576,944566,944571,953433,954308,954312,954313,954314,953928,953929,953930,955454,955750,910236,959680,959700,959701,959702,959893,959733,959703,959704,960894,960895,960412,971704,976703,976704,976706,976705]
    # print(set([len(str(item)) for item in my_list_ids]))
    # # {4, 5, 6}

    # print(len(my_list_ids))
    # print(len(set(my_list_ids)))

    # list(duplicates([1,1,2,1,2,3,4,2]))
    # [1, 1, 2, 2]


    # # Повертає дуплікати зі списку
    # print(list(duplicates(my_list_ids)))
    # # [843108, 848614, 840585, 647803, 692625, 885627, 866584, 871984, 839327, 846405, 905468, 875166]

    # url_card = "/product/biskvit-milka-z-kakao-ta-glazur-iu-z-molochnogo-shokoladu-975715"
    # id_tovar = url_card.split('-')[-1]
    # print(id_tovar)

if __name__ == "__main__":
    main()

# "\u0433" = "г"
# "\u043b" = "л"
# "\u0448\u0442" = "шт"
# "\u0448\u0442/\u0443\u043f" = "шт/уп"
# "\u0433/\u0443\u043f" = "г/уп"
# "\u043a\u0433" = "кг"
# "\u043c\u043b" = "мл"

# 0.2
# 0.25
# 0.5
# 0.95
# 1.5
# 2.0
