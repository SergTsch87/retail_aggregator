#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests
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



def main():
    # url = 'https://www.atbmarket.com/catalog/molocni-produkti-ta-ajca'
    # price_element = scrape_product_price_atb(url)
    # print(price_element)

    url = 'https://silpo.ua/category/molochni-produkty-ta-iaitsia-234'
    price_element = scrape_product_price_silpo(url)
    print(price_element)
    

if __name__ == "__main__":
    main()