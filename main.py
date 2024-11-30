#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests, time, csv, logging, socket
from bs4 import BeautifulSoup

from pathlib import Path

# Завдання 1: Перевір усі виключні ситуації, які прописав, зімітувавши їх

# Завдання 2: Об'єднати два різні коди парсингу для динамічних та статичних сайтів з допомогою декоратора

def is_connected():
    # Для перевірки доступності інтернету перед відправленням запиту
    try:
        socket.create_connection(('www.google.com', 80), timeout=5)
        return True
    except OSError:
        return False


def scrape_product_price_atb(url):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        # headers = {
        #     "Content-Type": "application/json",
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        # }
        headers = {
            "authority": "www.google.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }
        # response = requests.get(url, timeout=10, headers=headers)
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # !!!
        # Це все добре працює лише для однієї картки.
        # Для списку карток потрібні будуть цикл та find_all()
        bottom_sup = soup.select_one('div.catalog-item__product-price.product-price.product-price--weight.product-price--sale > data.product-price__bottom > span > sup')
        if bottom_sup:
            top_sup = bottom_sup.find_parent('div').select_one('data.product-price__bottom > span > sup')
            # print(top_sup.text if top_sup else "Тег не знайдено")
            if top_sup:
                price_element = top_sup.text
                if price_element:
                    return price_element.text.strip()
                else:
                    return "Price not found on the page"
            else:
                return "Tag not found on the page"
        else:
            # print("Перший тег не знайдено")
            return "First tag not found on the page"

        # 2-й варіант:
        # if price_element:
        #     return price_element.text.strip()
        # else:
        #     return "Price not found on the page"
    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"


def scrape_product_price_silpo(url):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # !!!
        # Це все добре працює лише для однієї картки.
        # Для списку карток потрібні будуть цикл та find_all()
        first_card_soup = soup.select_one('body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.ft-flex.ft-flex-col.ft-item-center.xl\\:ft-flex-row > div.ft-whitespace-nowrap.ft-text-22.ft-font-bold')
        if first_card_soup:
            price_element = first_card_soup.text
            if price_element:
                return price_element.strip()
            else:
                return "Price not found on the page"
        else:
            return "Tag not found on the page"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"


def scrape_product_price_fora(url):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        response = requests.get(url, timeout=100)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # !!!
        # Це все добре працює лише для однієї картки.
        # Для списку карток потрібні будуть цикл та find_all()
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(3) > div > div.product-list-item__body > div > div:nth-child(1) > div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(1) > div > div.product-list-item__body > div > div:nth-child(1) > div > div > div.current-integer')
        # first_card_soup = soup.select_one('div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul')
        first_card_soup = response.text
        print(f'first_card_soup == {first_card_soup}')
        if first_card_soup:
            # price_element = first_card_soup.text
            price_element = first_card_soup
            if price_element:
                # return price_element.strip()
                return price_element
            else:
                return "Price not found on the page"
        else:
            return "Tag not found on the page"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"


def scrape_product_price_metro(url):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        time.sleep(30)
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # !!!
        # Це все добре працює лише для однієї картки.
        # Для списку карток потрібні будуть цикл та find_all()
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(3) > div > div.product-list-item__body > div > div:nth-child(1) > div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(1) > div > div.product-list-item__body > div > div:nth-child(1) > div > div > div.current-integer')
        # first_card_soup = soup.select_one('div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul')
        first_card_soup = response.text
        print(f'first_card_soup == {first_card_soup}')
        if first_card_soup:
            # price_element = first_card_soup.text
            price_element = first_card_soup
            if price_element:
                # return price_element.strip()
                return price_element
            else:
                return "Price not found on the page"
        else:
            return "Tag not found on the page"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"


# !!!
# Частина товарів тут наче є, а частини нема...
def scrape_product_price_novus(url):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        # time.sleep(30)
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # !!!
        # Це все добре працює лише для однієї картки.
        # Для списку карток потрібні будуть цикл та find_all()
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(3) > div > div.product-list-item__body > div > div:nth-child(1) > div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul > div:nth-child(1) > div > div.product-list-item__body > div > div:nth-child(1) > div > div > div.current-integer')
        # first_card_soup = soup.select_one('div.current-integer')
        # first_card_soup = soup.select_one('#id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4 > div.container > div.content > div > div.category-page__content > div.product-list__wrapper > ul')
        first_card_soup = response.text
        print(f'first_card_soup == {first_card_soup}')
        if first_card_soup:
            # price_element = first_card_soup.text
            price_element = first_card_soup
            if price_element:
                # return price_element.strip()
                return price_element
            else:
                return "Price not found on the page"
        else:
            return "Tag not found on the page"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"


def scrape_content_page(url):
    try:
        # time.sleep(30)
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        first_card_soup = response.text
        print(f'first_card_soup == {first_card_soup}')
        if first_card_soup:
            # price_element = first_card_soup.text
            price_element = first_card_soup
            if price_element:
                # return price_element.strip()
                return price_element
            else:
                return "Price not found on the page"
        else:
            return "Tag not found on the page"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"
    

def fetch_html(url):
    """
        Завантажує HTML-вміст сторінки.
        Перевіряє статус HTTP-відповіді (напр., чи немає помилки 403/404).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        return f'Error fetching {url}: {e}'


def check_parsability(html):
    """
        Перевіряє наявність основного контенту, який містить інф-цію про продукти
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        potential_elements = soup.find_all(['ul', 'ol', 'div'], recursive=True, limit=5)
        if potential_elements:
            return 'Parsable'  # Є базовий html-контент
        return 'Likely JS-generated or no content found'
    except Exception as e:
        return f'Error parsing HTML: {e}'


def check_bots_protection(html):
    if 'captcha' in html.lower():
        return 'Protected by CAPTCHA'
    elif 'login' in html.lower() or 'sign in' in html.lower():
        return 'Requires login'
    return 'No apparent bot protection'


# def check_bots_protection(url):
#     html = fetch_html(url)
#     if 'captcha' in html.lower():
#         return 'Protected by CAPTCHA'
#     elif 'login' in html.lower() or 'sign in' in html.lower():
#         return 'Requires login'
#     return 'No apparent bot protection'


# def save_to_csv(results, fname = 'parsing_res.csv'):
#     """
#         Зберігає рез-ти перевірки до CSV для подальшого ан-зу
#     """
#     with open(fname, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Website', 'Status'])
#         for url, status in results.items():
#             writer.writerow([url, status])

def save_to_csv(results, fname = 'parsing_res.csv'):
    """
        Зберігає рез-ти перевірки до CSV для подальшого ан-зу
    """
    # Визначаємо шлях до файлу main.py
    current_dir = Path(__file__).parent  # Папка, в якій знаходиться наш скрипт
    file_path = current_dir / fname  # Задаємо ім'я та шлях до файлу

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # writer.writerow(['Name', 'URL', 'Result'])
        writer.writerow(['Name', 'URL', 'Result'])
        for result in results:
            writer.writerow(result)


def scrape_product_price(url, path):
    """
    Fetches the price of a product from a given store URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        str: The price of the product or an error message if not found.
    """
    try:
        # Fetch the HTML content of the page
        time.sleep(30)
        response = requests.get(url, timeout=20)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        first_card_soup = soup.select_one(path)

        if first_card_soup:
            price_element = first_card_soup.text
            # price_element = first_card_soup
            if price_element:
                return price_element.strip()
            else:
                return "Price not found on the page"
        else:
            return f"Tag not found on the page\nContent of HTML-page:\n\n{soup}"

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"

# =========================================================

# def fetch_page_content(url):
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
    
    if is_connected:  # Якщо є інтернет-зв'язок
        
        # Повтори при таймаутах
        for attempt in range(retries):
            try:
                # Set a timeout to prevent handling
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
                return response.text  # Успішний запит, - Повертаємо контент
            
            except requests.exceptions.Timeout:
                # Лише логуємо помилку, та повторюємо спробу
                logging.error(f"Attempt {attempt + 1}: Request timed out for {url}")
                # return 'Error: The request timed out.'

            except requests.exceptions.ConnectionError:
                logging.error(f"Attempt {attempt + 1}: Connection error for {url}")
                # return 'Error: A connection error occured.'
            
            except requests.exceptions.HTTPError as e:
                logging.error(f"Attempt {attempt + 1}: HTTP error {response.status_code}")
                # Повертаємо помилку одразу, бо це не мережевий збій
                return f'Error: HTTP error occured. Status code: {response.status_code}'
            
            except requests.exceptions.RequestException as e:
                # Catch-all for other request-related errors
                logging.error(f"Attempt {attempt + 1}: Unexpected request error: {e}")
                # if attempt == 2:
                #     raise e  # Остання спроба
                time.sleep(2 ** attempt)  #  Покрокове збільшення затримки, - задля уникнення блокування сервером
                return f'Error: An unexpected error occurred: {e}'
            
        # Якщо усі спроби були невдалі:
        return 'Error: Failed to fetch the URL after multiple retries.'
    
    else:
        return 'Error: No internet connection'
        

def parse_page(url, path):
    """
    Parses a webpage and extracts content using BeautifulSoup.

    Args:
        url (str): The URL of the webpage.

    Returns:
        str: The extracted content or an error message.
    """
    # html_content = fetch_page_content(url)
    html_content = fetch_url_with_retries(url, retries=3, timeout=10)
    if 'Error:' in html_content:
        # Return error message directly if fetch_page_content failed
        return html_content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Логіка парсингу для більшості статичних сайтів з наданого списку
        if soup.select_one(path):
            result = soup.select_one(path).text

            if result:
                return result.strip()
            else:
                raise ValueError('Extracted data is empty')  # return "Price not found on the page"
        
        else:
            raise AttributeError(f'HTML element not found\nContent of HTML-page:\n\n{soup}')   # return "Tag not found on the page\nContent of HTML-page:\n\n{soup}"


    except requests.exceptions.Timeout:
        return 'Error: Request timed out'
    
    except requests.exceptions.ConnectionError:
        # return 'Error: A connection error occured.'
        return 'Error: Could not connect to server'
    
    except requests.exceptions.HTTPError as e:
        return f'Error: HTTP error occured. Status code: {e.response.status_code}'

    except AttributeError as e:
        return f'Error: HTML structure issue - {e}'
    
    except ValueError as e:
        return f'Error: Data issue - {e}'

    except requests.exceptions.RequestException as e:
        return f"Error fetching the product page: {e}"

    except Exception as e:
        return f'Error: Failed to parse the page content. Details: {e}'


def main():
    logging.basicConfig(filename='parser_errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    # logging.error(f'Error: {e}')

    # І тут усе генерується динамічно...
    # url = 'https://www.atbmarket.com/catalog/molocni-produkti-ta-ajca'
    # price_element = scrape_product_price_atb(url)
    # print(f'The price of the product is: {price_element}')

    # url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
    # price_element = scrape_product_price_silpo(url)
    # print(f'The price of the product is: {price_element}')
    
    # url = 'https://fora.ua/category/molochni-produkty-ta-iaitsia-2656'
    # price_element = scrape_product_price_fora(url)
    # print(f'The price of the product is: {price_element}')
    # # І тут усе генерується динамічно...

    # url = 'https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F'
    # price_element = scrape_product_price_metro(url)
    # print(f'The price of the product is: {price_element}')

    # url = 'https://novus.ua/sales/molochna-produkcija-jajcja.html'
    # price_element = scrape_product_price_novus(url)
    # print(f'The price of the product is: {price_element}')


    # url = 'https://varus.ua/molochni-produkti'
    # path = '#category > div.main > div.products > div:nth-child(3) > div > div:nth-child(1) > div > div.sf-product-card__block > div > div > span'

    # url = 'https://novus.ua/sales/molochna-produkcija-jajcja.html'
    #         # old path: #product-price-4759 > span > span.integer
    # path = '#product-price-57667 > span > span.integer'

    # price_element = parse_page(url, path)
    # print(price_element)


# Тут ще можна пошукати:
#     https://www.fozzy.ua/ua/

    dict_urls_static = {
        'silpo': ['https://silpo.ua/category/molochni-produkty-ta-iaitsia-234', 'body > sf-shop-silpo-root > shop-silpo-root-shell > silpo-shell-main > div > div.main__body > silpo-category > silpo-catalog > div > div.container.catalog__products > product-card-skeleton > silpo-products-list > div > div:nth-child(1) > shop-silpo-common-product-card > div > a > div.product-card__body > div.ft-mb-8.product-card-price > div.ft-flex.ft-flex-col.ft-item-center.xl\\:ft-flex-row > div'],
        'spar': ['https://shop.spar.ua/rivne/section/Populyarni_tovary_Varash', '#main > div.container_center.clearfix > div > div > div > div.gallery.stock > div:nth-child(1) > div.teaser > div.info > div.price.clearfix > span.nice_price'],
        'eko_market': ['https://eko.zakaz.ua/uk/categories/dairy-and-eggs-ekomarket/', '#PageWrapBody_desktopMode > div.jsx-b98800c5ccb0b885.ProductsBox > div > div:nth-child(1) > div > a > span > div.jsx-cdc81c93bd075911.ProductTile__details > div.jsx-cdc81c93bd075911.ProductTile__prices > div > span.jsx-9c4923764db53380.Price__value_caption'],
        'nashkraj': ['https://shop.nashkraj.ua/lutsk/category/molokoprodukti-yaytsya', '#main > div.container_center.clearfix > div > div > div.col-lg-9.col-md-9.col-sm-8.col-xs-6.pad_0.media_870 > div:nth-child(3) > div.gallery.stock > div:nth-child(1) > div.teaser > div.info > div.price.clearfix > span.nice_price'],
        'pankovbasko': ['https://pankovbasko.com/ua/catalog/molochnaya-produkchuya/all', '#content > ul.row.block-grid.list-unstyled > li:nth-child(1) > div > div.product-price > span.price'],
        'megamarket': ['https://megamarket.ua/catalog/moloko', 'body > div.main_wrapper.grids > div.main > div.main_row > div > ul > li:nth-child(1) > div.product_info > form > div.price_block > div > div.price.cp']
    }

    dict_urls_dynamic = {
        'novus': ['https://novus.ua/sales/molochna-produkcija-jajcja.html', '#product-price-4759 > span > span.integer'],
        'varus_1': ['https://varus.ua/rasprodazha?cat=53036', '#category > div.main.section > div.products > div.block > div:nth-child(2) > div > div:nth-child(1) > div > div.sf-product-card__block > div > div > ins'],
        'varus_2': ['https://varus.ua/molochni-produkti', '#category > div.main > div.products > div:nth-child(3) > div > div:nth-child(1) > div > div.sf-product-card__block > div > div > span'],
        'metro': ['https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F', '#main > div > div.content-container > div:nth-child(2) > div.mfcss.mfcss_wrapper > div.fixed-width-container > div > div > div:nth-child(2) > div > div.col-lg-9 > div.mfcss_card-article-2--grid-container-flex > span:nth-child(1) > div > div > div.bottom-part > div > div.price-display-main-row > span.primary.promotion.volume-discount > span > span'],
        'velmart': ['https://velmart.ua/product-of-week/', '#main > div > div > div > section.elementor-section.elementor-top-section.elementor-element.elementor-element-ecfc4c.elementor-section-stretched.elementor-section-boxed.elementor-section-height-default.elementor-section-height-default.jet-parallax-section > div.elementor-container.elementor-column-gap-default > div > div > div > div > div > div > div > div > div:nth-child(1) > div > h5 > a'],
        'zatak': ['https://zatak.org.ua/categories/61f84a85-5d59-444f-9ab6-b2d83b57f2c5', '#main-goods-list-container > div > div.goods-list__container.noBreadcrumbs > app-goods-list-container > div > div.goods-container__goods > app-goods-list > div.goods-list.ng-star-inserted > div:nth-child(1) > app-goods-list-item > div > app-goods-list-item-template > div.goods-list-item__body > div > p.goods-list-item__price-value'],
        'myasnakorzyna': ['https://myasnakorzyna.net.ua/catalog', '#main > div > section > div > div.layout-box__catalog > div.layout-box__catalog-content > div:nth-child(1) > div.price > div'],
        'kopiyka': ['https://my.kopeyka.com.ua/shares/category/5?name=%D0%9C%D0%BE%D0%BB%D0%BE%D0%BA%D0%BE%20%D0%AF%D0%B9%D1%86%D1%8F', 'body > app > wrapper > main > div > share > div > div:nth-child(2) > products > div > div > div:nth-child(1) > div.product-prices > div > div.product-price-new']
    }

    dict_urls_img ={
        'kishenya_1': ['https://kishenya.ua/tovar-tyzhnia/', '#rl-gallery-1 > div:nth-child(1) > a > img'],
        'kishenya_2': ['https://kishenya.ua/vkett/', '#rl-gallery-1 > div:nth-child(1) > a > img']
    }

    results = []
    for key, value in dict_urls_static.items():
        url = value[0]
        path = value[1]
        # tmp_str = f'\n{key}: {scrape_product_price(url, path)}\n'
        # tmp_str = f'\n{key}: {parse_page(url, path)}\n'
        tmp_elem = [key, url, parse_page(url, path)]
        results.append(tmp_elem)
        # print(tmp_str)

    print('Цикл пройдено')
    fname_1 = 'parsing_res_static.csv'
    save_to_csv(results, fname_1)
    print('Файл збережено')

    
    # results = []
    # for key, value in dict_urls_dynamic.items():
    #     url = value[0]
    #     path = value[1]
    #     # tmp_str = f'\n{key}: {scrape_product_price(url, path)}\n'
    #     tmp_str = f'\n{key}: {parse_page(url, path)}\n'
    #     results.append(tmp_str)
        # tmp_elem = [key, url, path]
        # results.append(tmp_elem)
    #     # print(tmp_str)
    # print('Цикл пройдено')
    
    # fname_2 = 'parsing_res_dynamic.csv'
    # save_to_csv(results, fname_2)
    # print('Файл збережено')


    # results = []
    # for key, value in dict_urls_img.items():
    #     url = value[0]
    #     path = value[1]
    #     tmp_str = f'\n{key}: {scrape_product_price(url, path)}\n'
    #     results.append(tmp_str)
        # tmp_elem = [key, url, path]
        # results.append(tmp_elem)
    #     print(tmp_str)
    
    # fname_3 = 'parsing_res_img.csv'
    # save_to_csv(results, fname_3)



#     urls = [
# 'https://varus.ua/rasprodazha?cat=53036',
# 'https://varus.ua/molochni-produkti',
# 'https://novus.ua/sales/molochna-produkcija-jajcja.html',
# 'https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F',
# 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234',
# 'https://velmart.ua/product-of-week/',
# 'https://kishenya.ua/tovar-tyzhnia/',
# 'https://kishenya.ua/vkett/',
# 'https://zatak.org.ua/categories/61f84a85-5d59-444f-9ab6-b2d83b57f2c5',
# 'https://shop.spar.ua/rivne/section/Populyarni_tovary_Varash',
# 'https://eko.zakaz.ua/uk/categories/dairy-and-eggs-ekomarket/',
# 'https://shop.nashkraj.ua/lutsk/category/molokoprodukti-yaytsya',
# 'https://myasnakorzyna.net.ua/catalog',
# 'https://pankovbasko.com/ua/catalog/molochnaya-produkchuya/all',
# 'https://megamarket.ua/catalog/moloko',
# 'https://my.kopeyka.com.ua/shares/category/5?name=%D0%9C%D0%BE%D0%BB%D0%BE%D0%BA%D0%BE%20%D0%AF%D0%B9%D1%86%D1%8F'
#     ]

    # # Завантажуємо HTML
    # # та перевіряємо наявність ключових елементів
    # for url in urls:
    #     print(f'\nChecking {url}...')
    #     html = fetch_html(url)
    #     if html.startswith('Error'):
    #         print(f'Error!  {html}\n')   # Проблема із завантаженням
    #     else:
    #         result_1 = check_parsability(html)
    #         result_2 = check_bots_protection(html)
    #         print(f'{url}: {result_1}\n {result_2}\n')
    #     # content_page = scrape_product_price_novus(url)
    #     # print(f'The price of the product is: {content_page}')
    
if __name__ == "__main__":
    main()

# Parsable
#     Protected by CAPTCHA
# https://eko.zakaz.ua/uk/categories/dairy-and-eggs-ekomarket/
# https://varus.ua/rasprodazha?cat=53036
# https://varus.ua/molochni-produkti
# https://novus.ua/sales/molochna-produkcija-jajcja.html
# https://kishenya.ua/tovar-tyzhnia/
# https://kishenya.ua/vkett/

# Parsable
#     Requires login
# https://shop.nashkraj.ua/lutsk/category/molokoprodukti-yaytsya
# https://silpo.ua/category/molochni-produkty-ta-iaitsia-234
# https://velmart.ua/product-of-week/
# https://shop.spar.ua/rivne/section/Populyarni_tovary_Varash
# https://myasnakorzyna.net.ua/catalog
# https://megamarket.ua/catalog/moloko
# https://pankovbasko.com/ua/catalog/molochnaya-produkchuya/all
# https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F
# https://my.kopeyka.com.ua/shares/category/5?name=%D0%9C%D0%BE%D0%BB%D0%BE%D0%BA%D0%BE%20%D0%AF%D0%B9%D1%86%D1%8F
# https://zatak.org.ua/categories/61f84a85-5d59-444f-9ab6-b2d83b57f2c5


# Results:

    # novus: 569
    # silpo: 49.99 грн
    # spar: 28.1 грн
    # eko_market: 6.44
    # nashkraj: 6.2 грн
    # pankovbasko: 55.50
    # megamarket: 49""90 грн

    # varus_1: Tag not found on the page
    # varus_2: Tag not found on the page
    # metro: Tag not found on the page
    # velmart: Tag not found on the page
    # kishenya_1: Price not found on the page
    # kishenya_2: Price not found on the page
    # zatak: Tag not found on the page
    # myasnakorzyna: Error fetching the product page: 403 Client Error: Forbidden for url: https://myasnakorzyna.net.ua/catalog
    # kopiyka: Tag not found on the page