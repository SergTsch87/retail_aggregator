#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests, time, csv, logging, socket, json, sys
from bs4 import BeautifulSoup
from functools import lru_cache

from pathlib import Path


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
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            html = response.text
            
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


# @timer_elapsed
def parse_product_card(html_card):
    # Extract Data from a Single Product Card
    # Саме в цій функції ми визначаємо усі ті дані, які хочемо дістати з кожної товарної картки
    soup = BeautifulSoup(html_card, 'html.parser')
    return {  # for Silpo
        "url_page_category": 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234',
        "current_price": extract_element(soup,
                                         "div",
                                         "ft-whitespace-nowrap ft-text-22 ft-font-bold"),
        "old_price": extract_element(soup,
                                         "div",
                                         "ft-line-through ft-text-black-87 ft-typo-14-regular xl:ft-typo"),
        
        "url_card": soup.find("a")["href"] if soup.find("a") else '',
        
        "title": extract_element(soup,
                                         "div",
                                         "product-card__title"),
        "volume": extract_element(soup,
                                         "div",
                                         "ft-typo-14-semibold xl:ft-typo-16-semibold"),
        "discount": extract_element(soup,
                                         "div",
                                         "product-card-price__sale"),
        "rating": extract_element(soup,
                                         "span",
                                         "catalog-card-rating--value")
    }
        

# @timer_elapsed
def parse_page(html_page):
    # Extract All Product Cards on a Page
    # Parse all cards in a container.
    
    products = []
    
    soup = BeautifulSoup(html_page, 'html.parser')
    product_cards = soup.find_all('div', class_="products-list__item")  # for Silpo
    products = [parse_product_card(str(card)) for card in product_cards]
    
    if not products or "Товари закінчилися" in html_page:   # Перевірка на порожній список або помилковий номер сторінки
        return []
    
    return products


def get_max_pagination(base_url):
    # """
    # Повертає найбільшу к-сть сторінок певної категорії
    # """
    response = requests.get(base_url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
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
        
        save_to_file(products, 'data.jsonl')
        # print('Code in fetch_all_pages, In While Loop, After call parse_page')
        dict_entries['count_pages'] = dict_entries.get('count_pages', 0) + 1
        dict_entries['count_entries'] = dict_entries.get('count_entries', 0) + len(products)
        # dict_entries['sizeof'] = dict_entries.get('sizeof', 0) + sys.getsizeof(products)

        # print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\nsizeof = {dict_entries['sizeof']}\n")
        print(f"\ncount_pages = {dict_entries['count_pages']}\ncount_entries = {dict_entries['count_entries']}\n")
        
        # all_pages_data[f'page_{page_number}'] = products
        all_products.extend(products)
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
        for record in data:
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


    # Expanding Gradually
    # Pass the URL of the next store as an argument to fetch_all_pages
    
    base_url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
    all_products = fetch_all_pages(base_url, start_page=1)

    # print(f'num = {get_max_pagination(base_url)}')
    # #  Найбільше число у пагінації

    # print('Дані зібрано')
    # # save_to_file(all_products, 'data.jsonl')
    # print('Дані збережено до файлу "data.jsonl"')


if __name__ == "__main__":
    main()