#!usr/bin/env python3

# env1\bin\python -m pip freeze > requirements.txt
# env2\bin\python -m pip install -r requirements.txt

import requests
from bs4 import BeautifulSoup


def scrape_product_price(url):
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


def main():
    pass


if __name__ == "__main__":
    main()