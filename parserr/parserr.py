import json
import requests
import time
from bs4 import BeautifulSoup
from requests import RequestException


def get_proxy():
    proxy = requests.get(
        'https://gimmeproxy.com/api/getProxy?country=RU&get=true&supportsHttps=true&protocol=http')
    proxy_json = json.loads(proxy.content)
    if proxy.status_code != 200 and 'ip' not in proxy_json:
        raise RequestException
    else:
        return 'http://' + proxy_json['ip'] + ':' + proxy_json['port']


def get_html(url):
    import random
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv)',
        'Mozilla/5.0 (X11; Linux i686; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    ]
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    proxy = {
        'https': get_proxy()
    }
    response = requests.get(url, headers=headers)
    return response.content


def get_ads_list(avito_search_url):
    """
    :param avito_search_url: url like https://m.avito.ru/kazan/avtomobili/inomarki?pmax=200000&pmin=50000
    :return: ads list
    """
    html = get_html(avito_search_url)

    # f = open("avito-1.html", "r")
    # html = f.read()

    soup = BeautifulSoup(html, 'lxml')

    f = open("avito-test.html", "w+")
    f.write(soup.prettify())
    f.close()

    print(f'html lenght {len(soup.prettify())}')

    ads = soup.select('.item.item_table')

    print(f'ads count {len(ads)}')

    ads_list = []
    for ad in ads:
        id, name, url, price, img_url, is_vip = None, None, None, None, None, False

        id = ad.attrs.get('id')
        if not id:
            print("id for not found, ad has been skipped")
            continue

        link = next((a for a in ad.select('a.snippet-link') if a.get('title')), None)
        if link:
            name = link['title']
            url = f"https://www.avito.ru{link['href']}"
        
        price_span = next(iter(ad.select('span[data-marker="item-price"]')), None)
        if price_span:
            price = price_span.string.strip()
            is_vip = 'snippet-price-vas' in price_span.attrs['class']
        
        img = next(iter(ad.select('img')), None)
        img_url = img['src'] if img else ""

        created_span = next(iter(ad.select('.snippet-date-info')), None)
        created = created_span['data-tooltip'] if created_span else ""

        if not is_vip:
            # print("%-70s %-15s %-15s" % (name, price, id))
            ads_list.append({
                'id': id,
                'title': name,
                'price': price,
                'url': url,
                'img': img_url,
            })

    return ads_list


def get_new_ads(new, old):
    _ = []
    for ad in new:
        if ad not in old:
            _.append(ad)
    return _


if __name__ == '__main__':
    get_ads_list('https://www.avito.ru/kazan/igry_pristavki_i_programmy/igrovye_pristavki-ASgBAgICAUSSAsoJ?q=ps4+pro')