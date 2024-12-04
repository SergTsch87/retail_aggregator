#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests, time, csv, logging, socket, json
from bs4 import BeautifulSoup

from pathlib import Path



# Ще один магазин (стат чи динамо?..):
    # https://fozzyshop.ua

# +  Завдання 1: Прибери зайві коментарі та код

# Завдання 2: Перевір усі виключні ситуації, які прописав, зімітувавши їх

# Завдання 3: Об'єднай два різні коди парсингу для динамічних та статичних сайтів з допомогою декоратора


def is_connected():
    # Для перевірки доступності інтернету перед відправленням запиту
    try:
        socket.create_connection(('www.google.com', 80), timeout=5)
        return True
    except OSError:
        return False


def get_file_path(fname):
    # Визначаємо повний шлях до файлу fname
    current_dir = Path(__file__).parent  # Папка, в якій знаходиться наш скрипт
    file_path = current_dir / fname  # Задаємо ім'я та шлях до файлу
    return file_path



def handle_exception(e, context=""):
    """
    Handles exceptions and returns a formatted error message.

    Args:
        e (Exception): The exception to handle.
        context (str): Additional context about where the error occurred.

    Returns:
        str: Formatted error message
    """
    if isinstance(e, requests.exceptions.Timeout):
        error_message = "Error: Request timed out."
    elif isinstance(e, requests.exceptions.ConnectionError):
        error_message = "Error: Could not connect to the server."
    elif isinstance(e, requests.exceptions.HTTPError):
        error_message = f"Error: HTTP error occurred. Status code: {e.response.status_code if e.response else 'Unknown'}."
    elif isinstance(e, AttributeError):
        error_message = f"Error: HTML structure issue - {e}."
    elif isinstance(e, ValueError):
        error_message = f"Error: Data issue - {e}."
    elif isinstance(e, requests.exceptions.RequestException):
        error_message = f"Error: Unexpected request error - {e}."
    else:
        error_message = f"Error: An unexpected error occurred - {e}."

    logging.error(f"{context} {error_message}")
    return error_message


def save_to_csv(results, fname = 'parsing_res.csv'):
    """
        Зберігає рез-ти перевірки до CSV для подальшого ан-зу
    """
    # Повний шлях до файлу fname
    file_path = get_file_path(fname)

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'URL', 'Result'])
        for result in results:
            writer.writerow(result)


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
            # Set a timeout to prevent handling
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            return response.text  # Успішний запит, - Повертаємо контент
        
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}.")
            if attempt == retries - 1:  # Last attempt
                return handle_exception(e, context=f"Fetching URL {url}")
            time.sleep(2 ** attempt)  #  Покрокове збільшення затримки, - задля уникнення блокування сервером

    # Якщо усі спроби були невдалі:
    return 'Error: Failed to fetch the URL after multiple retries.'
        

# def parse_page(url, path):
def parse_page(url_page_category,
                path_current_price,
                path_old_price,
                url_card,
                path_title):
    """
    Parses a webpage and extracts content using BeautifulSoup.

    Args:
        url (str): The URL of the webpage.

    Returns:
        str: The extracted content or an error message.
    """
    html_content = fetch_url_with_retries(url_page_category)
    if 'Error:' in html_content:
        # # Log error and return None
        # logging.error(f"Error while fetching URL {url_page_category}: {html_content}")
        # return None
        return html_content   # Return error message directly if fetch_page_content failed
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        elem_val_curr_price = soup.select_one(path_current_price)

        if not elem_val_curr_price:
            raise AttributeError(f"Value current price with path '{path_current_price}' not found.")
        val_current_price = elem_val_curr_price.text.strip()
        if not val_current_price:
            raise ValueError("Extracted value current price is empty.")
        return val_current_price
    except Exception as e:
        return handle_exception(e, context=f"Parsing URL {url_page_category}")


def save_dict_info_to_csv(dict_urls, fname):
    results = []
    for key, value in dict_urls.items():
        url_page_category = value['url_page_category']
        path_current_price = value['path_current_price']
        path_old_price = value['path_old_price']
        url_card = value['url_card']
        path_title = value['path_title']
        # tmp_elem = [key, url, parse_page(url, path)]
        tmp_elem = [key, url_page_category, parse_page(url_page_category,
                                                       path_current_price,
                                                       path_old_price,
                                                       url_card,
                                                       path_title)]
        results.append(tmp_elem)

    print('Цикл пройдено')
    save_to_csv(results, fname)
    print('Файл збережено')


def load_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def main():
    # Повний шлях до файлу fname
    fname = 'parser_errors.log'
    file_path = get_file_path(fname)
    
    logging.basicConfig(
        filename=file_path,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    
    # !!!
    # Тут теж перевір!
    # https://fozzyshop.ua

# Silpo:
#     current_price:
#         body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.ft-flex.ft-flex-col.ft-item-center.xl\\:ft-flex-row > div
#     old_price:
#         body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.product-card-price__old > div.ft-line-through.ft-text-black-87.ft-typo-14-regular.xl\\:ft-typo
#     title:
#         body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.product-card__title
#     link:
#         body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a

# energy_value
# proteins
# fats
# mass_fraction_of_fat
# carbohydrates


    # url_page_category: 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
    # url_card: 'https://silpo.ua/product/maslo-solodkovershkove-bilo-ekstra-82-871874'

# old_price
# url_card
# title

    dict_urls_static = {
        'silpo': {
                    "url_page_category": 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234',
                    "current_price": 'body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.ft-flex.ft-flex-col.ft-item-center.xl\\:ft-flex-row > div',
                    "old_price": 'body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.product-card-price__old > div.ft-line-through.ft-text-black-87.ft-typo-14-regular.xl\:ft-typo',
                    "url_card": 'body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a',
                    "title": 'body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.product-card__title'
        },
        'spar': {
                    "url_page_category": 'https://shop.spar.ua/rivne/section/Populyarni_tovary_Varash',
                    "current_price": '#main > div.container_center.clearfix > div > div > div > div.gallery.stock > div:nth-child(1) > div.teaser > div.info > div.price.clearfix > span.nice_price',
                    "old_price": '',
                    "url_card": '',
                    "title": ''
        },
        'eko_market': {
                    "url_page_category": 'https://eko.zakaz.ua/uk/categories/dairy-and-eggs-ekomarket/',
                    "current_price": '#PageWrapBody_desktopMode > div.jsx-b98800c5ccb0b885.ProductsBox > div > div:nth-child(1) > div > a > span > div.jsx-cdc81c93bd075911.ProductTile__details > div.jsx-cdc81c93bd075911.ProductTile__prices > div > span.jsx-9c4923764db53380.Price__value_caption',
                    "old_price": '',
                    "url_card": '',
                    "title": ''
        },
        'nashkraj': {
                    "url_page_category": 'https://shop.nashkraj.ua/lutsk/category/molokoprodukti-yaytsya',
                    "current_price": '#main > div.container_center.clearfix > div > div > div.col-lg-9.col-md-9.col-sm-8.col-xs-6.pad_0.media_870 > div:nth-child(3) > div.gallery.stock > div:nth-child(1) > div.teaser > div.info > div.price.clearfix > span.nice_price',
                    "old_price": '',
                    "url_card": '',
                    "title": ''
        },
        'pankovbasko': {
                    "url_page_category": 'https://pankovbasko.com/ua/catalog/molochnaya-produkchuya/all',
                    "current_price": '#content > ul.row.block-grid.list-unstyled > li:nth-child(1) > div > div.product-price > span.price',
                    "old_price": '',
                    "url_card": '',
                    "title": ''
        },
        'megamarket': {
                    "url_page_category": 'https://megamarket.ua/catalog/moloko',
                    "current_price": 'body > div.main_wrapper.grids > div.main > div.main_row > div > ul > li:nth-child(1) > div.product_info > form > div.price_block > div > div.price.cp',
                    "old_price": '',
                    "url_card": '',
                    "title": ''
        }
    }


    dict_urls_dynamic = {
        # https://www.atbmarket.com/catalog
        # https://fora.ua/
        'novus': {
            "url_page_category": 'https://novus.ua/sales/molochna-produkcija-jajcja.html',
            "current_price": '#product-price-4759 > span > span.integer',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'varus_1': {
            "url_page_category": 'https://varus.ua/rasprodazha?cat=53036',
            "current_price": '#category > div.main.section > div.products > div.block > div:nth-child(2) > div > div:nth-child(1) > div > div.sf-product-card__block > div > div > ins',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'varus_2': {
            "url_page_category": 'https://varus.ua/molochni-produkti',
            "current_price": '#category > div.main > div.products > div:nth-child(3) > div > div:nth-child(1) > div > div.sf-product-card__block > div > div > span',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'metro': {
            "url_page_category": 'https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F',
            "current_price": '#main > div > div.content-container > div:nth-child(2) > div.mfcss.mfcss_wrapper > div.fixed-width-container > div > div > div:nth-child(2) > div > div.col-lg-9 > div.mfcss_card-article-2--grid-container-flex > span:nth-child(1) > div > div > div.bottom-part > div > div.price-display-main-row > span.primary.promotion.volume-discount > span > span',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'velmart': {
            "url_page_category": 'https://velmart.ua/product-of-week/',
            "current_price": '#main > div > div > div > section.elementor-section.elementor-top-section.elementor-element.elementor-element-ecfc4c.elementor-section-stretched.elementor-section-boxed.elementor-section-height-default.elementor-section-height-default.jet-parallax-section > div.elementor-container.elementor-column-gap-default > div > div > div > div > div > div > div > div > div:nth-child(1) > div > h5 > a',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'zatak': {
            "url_page_category": 'https://zatak.org.ua/categories/61f84a85-5d59-444f-9ab6-b2d83b57f2c5',
            "current_price": '#main-goods-list-container > div > div.goods-list__container.noBreadcrumbs > app-goods-list-container > div > div.goods-container__goods > app-goods-list > div.goods-list.ng-star-inserted > div:nth-child(1) > app-goods-list-item > div > app-goods-list-item-template > div.goods-list-item__body > div > p.goods-list-item__price-value',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'myasnakorzyna': {
            "url_page_category": 'https://myasnakorzyna.net.ua/catalog',
            "current_price": '#main > div > section > div > div.layout-box__catalog > div.layout-box__catalog-content > div:nth-child(1) > div.price > div',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'kopiyka': {
            "url_page_category": 'https://my.kopeyka.com.ua/shares/category/5?name=%D0%9C%D0%BE%D0%BB%D0%BE%D0%BA%D0%BE%20%D0%AF%D0%B9%D1%86%D1%8F',
            "current_price": 'body > app > wrapper > main > div > share > div > div:nth-child(2) > products > div > div > div:nth-child(1) > div.product-prices > div > div.product-price-new',
            "old_price": '',
            "url_card": '',
            "title": ''
        }
    }

    dict_urls_img ={
        'kishenya_1': {
            "url_page_category": 'https://kishenya.ua/tovar-tyzhnia/',
            "current_price": '#rl-gallery-1 > div:nth-child(1) > a > img',
            "old_price": '',
            "url_card": '',
            "title": ''
        },
        'kishenya_2': {
            "url_page_category": 'https://kishenya.ua/vkett/',
            "current_price": '#rl-gallery-1 > div:nth-child(1) > a > img',
            "old_price": '',
            "url_card": '',
            "title": ''
        }
    }

    
    dict_urls = dict_urls_static
    # if ('\\' not in dict_urls) and ('\' in dict_urls):
    #     pass <треба замінити '\' на '\\'>
    fname = 'parsing_res_static.csv'
    save_dict_info_to_csv(dict_urls, fname)

    dict_urls = dict_urls_dynamic
    fname = 'parsing_res_dynamic.csv'
    save_dict_info_to_csv(dict_urls, fname)

    dict_urls = dict_urls_img
    fname = 'parsing_res_img.csv'
    save_dict_info_to_csv(dict_urls, fname)

    
if __name__ == "__main__":
    main()


    # silpo: 49.99 грн
    # spar: 28.1 грн
    # eko_market: 6.44
    # nashkraj: 6.2 грн
    # pankovbasko: 55.50
    # megamarket: 49""90 грн


    # Сільпо: 
    #     Молочне та яйця = 2373 карток
    #     Фрукти та овочі = 3257
    #     Мясо = 1429
    #     Риба = 2429
    #     Готові страви = 4300
    #     Сири = 1561
    #     Хліб та випічка = 3661
    #     Власні (магазинні) марки = 1457
    #     Лавка традицій (фермерське та власне, ФОП виробництво ) = 1685
    #     Здорове харчування (орган, веган, безлактоз, безглютен, без цукру, дієтичне) = 2102
    #     Ковбаси = 3023
    #     Соуси та спеції = 2859
    #     Солодощі = 5974
    #     Снеки та чіпси = 1441
    #     Кава та чай = 2274
    #     Напої = 2674
    #     Заморожена продукція = 1894
        
    #         Разом: 44 393

    # megamarket
    #     Разом: майже 8800

    # eko_market
    #     Разом: майже 6400

    # !!! nashkraj та Spar - ідентичний дизайн сайтів, навігації тощо)
    # nashkraj
    #     Разом: майже 4700

    # Spar
    #     Разом: майже 2450

    # pankovbasko
    #     Разом: майже 2000  (молочних, м'ясних, ковбасних та рибних виробів)

    # !!!
    # В усіх статичних сайтах магазинів,
    #     Разом: майже 70 тис. (68.800) карток товарів


# Які дані збиратиму:
    # Адреса сторінки каталогу
    # Назва товару
    # Стара ціна      (за наявності)
    # Нова / Поточна ціна

# Також слід додати:
    # Дата та час парсингу