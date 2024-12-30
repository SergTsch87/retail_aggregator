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
    soup = fetch_content(url, timeout=20, return_soup=True)
    # print(f'soup.prettify == {soup.find('ul', class_='menu-categories ng-star-inserted')}')

    dict_all_categories = {}
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

        if pos_last_num == len(volume) and volume[0].isalpha():
            pos_last_num = 0

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
    dict_conversation_factors = {    # Словник з коефіцієнтами конвертації до базових одиниць
        'кг': ('г', 1000),
        # 'мл': ('мл', 1),
        'л': ('мл', 1000)
    }

    if isinstance(volume_part, (int, float)) and len(ratio_part) > 0:
        for unit, (base_unit, factor) in dict_conversation_factors.items():

            if 'мл' in ratio_part:
                return int(volume_part), ratio_part

            elif unit in ratio_part:
                ratio_part = ratio_part.replace(unit, base_unit)
                volume_part *= factor
                return int(volume_part), ratio_part  # Припинити після першої знайденої відповідности

    return volume_part, ratio_part  # тут повертає також і "2.0 г/уп", "2.0 г/шт"


def get_id_tovar(url_card):
    return str( hash( 'silpo.ua' + url_card[10:] ) % 10 ** 8 )   # обтинає хеш до 8-ми цифр


def get_real_discount(current_price, old_price):
    if isinstance(current_price, (int, float)) and isinstance(old_price, (int, float)):
        return int(((old_price - current_price) / old_price) * 100)


def get_price_per_weight(current_price, volume_part, ratio_part):
    if isinstance(current_price, (int, float)) and isinstance(volume_part, (int, float)) and ('г' in ratio_part or 'мл' in ratio_part):
        # Якщо current_price та volume_part - числа, а рядок ratio_part не містить 'шт' / 'уп', тоді:
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
    if len(discount) >= 3:
        discount = int(discount[2:-1])
        real_discount = get_real_discount(current_price, old_price)
        differ_discounts = real_discount - discount
    else:
        differ_discounts = ''

    volume_part, ratio_part = converting_volume_measure(volume_part, ratio_part)
    price_per_weight = get_price_per_weight(current_price, volume_part, ratio_part)
    title = extract_element(soup, "div", "product-card__title")
    
    try:
        url_card = soup.find("a")["href"] if soup.find("a") else ''
        id_tovar = get_id_tovar(url_card)
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
    for card in product_cards:
        current_card = parse_product_card(str(card))
        if current_card['id_tovar'] not in set_ids:
            # Винесемо id_tovar зі словника:
            tmp_id_tovar = current_card['id_tovar']
            del current_card['id_tovar']
            products[tmp_id_tovar] = current_card
            set_ids.add( tmp_id_tovar )
    
    if not products or "Товари закінчилися" in html_page:   # Перевірка на порожній список або помилковий номер сторінки
        return []
    
    return products


def get_max_pagination(base_url):
    # """
    # Повертає найбільшу к-сть сторінок певної категорії
    # """
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
    dict_entries ={
        'count_entries': 0,
        'sizeof': 0
    }
    
    max_num_pages = get_max_pagination(base_url) #  Найбільше число у пагінації
    
    while page_number <= max_num_pages:
        url = f"{base_url}?page={page_number}"
        print(f'Fetching URL: {url}')
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

        products = parse_page(html)
        
        url_page_category = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
        save_to_file(products, url_page_category.split('/')[4] + '.jsonl')
        dict_entries['count_pages'] = dict_entries.get('count_pages', 0) + 1
        dict_entries['count_entries'] = dict_entries.get('count_entries', 0) + len(products)

        print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\n")
        
        all_products.append(products)
        page_number += 1

        previous_url = final_url  # Зберігаємо URL для порівняння у наступному циклі

    return all_products


@timer_elapsed
def save_to_file(data, fname='data.jsonl'):
    # Save data to a file after each page to avoid overloading RAM.
    # Use JSON Lines for incremental saving
    file_path = get_file_path(fname)
    with file_path.open(mode='a', encoding='utf-8') as file:
        if type(data) is list:
            for record in data:
                file.write(json.dumps(record) + '\n')
        elif type(data) is dict:
            for record in data.items():
                file.write(json.dumps(record) + '\n')
    

@timer_elapsed
def fetch_all_stores(store_urls):
    # Process Multiple Stores
    # Extend to iterate over multiple base URLs
    all_stores = {}
    for store_id, base_url in store_urls.items():
        all_stores[store_id] = fetch_all_pages(base_url, start_page=1)
    return all_stores


def load_data_with_jsonl(fname):
    # Витягає дані, які відповідають певній умові коду str_statement    
    file_path = str(get_file_path(fname))
    new_list = []
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found')
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
    # Сортує записи у порядку спадання вартости (за 1 кг / 1 л)
    file_path = str(get_file_path(fname))
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parsed_line = json.loads(line)
                data.append(parsed_line)
        return sorted(data, key=lambda x: [x[1]['price_per_weight'] is None, x[1]['price_per_weight'] == '', x[1]['price_per_weight']], reverse=True)


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
