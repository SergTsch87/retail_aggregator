#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests, time, csv
from bs4 import BeautifulSoup


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


def save_to_csv(results, fname = 'parsing_res.csv'):
    """
        Зберігає рез-ти перевірки до CSV для подальшого ан-зу
    """
    with open(fname, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Website', 'Status'])
        for url, status in results.items():
            writer.writerow([url, status])


def main():
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


# Тут ще можна пошукати:
#     https://www.fozzy.ua/ua/

    urls = [
'https://varus.ua/rasprodazha?cat=53036',
'https://varus.ua/molochni-produkti',
'https://novus.ua/sales/molochna-produkcija-jajcja.html',
'https://shop.metro.ua/shop/category/%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8/%D0%BC%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%96-%D0%BF%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8-%D1%82%D0%B0-%D1%8F%D0%B9%D1%86%D1%8F',
'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234',
'https://velmart.ua/product-of-week/',
'https://kishenya.ua/tovar-tyzhnia/',
'https://kishenya.ua/vkett/',
'https://zatak.org.ua/categories/61f84a85-5d59-444f-9ab6-b2d83b57f2c5',
'https://shop.spar.ua/rivne/section/Populyarni_tovary_Varash',
'https://eko.zakaz.ua/uk/categories/dairy-and-eggs-ekomarket/',
'https://shop.nashkraj.ua/lutsk/category/molokoprodukti-yaytsya',
'https://myasnakorzyna.net.ua/catalog',
'https://pankovbasko.com/ua/catalog/molochnaya-produkchuya/all',
'https://megamarket.ua/catalog/moloko',
'https://www.evrotek.com/ua/arsen/sobstvennoe-proizvodstvo-assortiment/molochne-virobnictvo.html',
'https://my.kopeyka.com.ua/shares/category/5?name=%D0%9C%D0%BE%D0%BB%D0%BE%D0%BA%D0%BE%20%D0%AF%D0%B9%D1%86%D1%8F',
'https://posad.com.ua/products/ovochi-frukti-suhofrukti/'
    ]

    # Завантажуємо HTML
    # та перевіряємо наявність ключових елементів
    for url in urls:
        print(f'\nChecking {url}...')
        html = fetch_html(url)
        if html.startswith('Error'):
            print(f'Error!  {html}\n')   # Проблема із завантаженням
        else:
            result_1 = check_parsability(html)
            result_2 = check_bots_protection(html)
            print(f'{url}: {result_1}\n {result_2}\n')
        # content_page = scrape_product_price_novus(url)
        # print(f'The price of the product is: {content_page}')
    
if __name__ == "__main__":
    main()