import json
import os
import random
import time

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from config import Config


def get_proxy():
    proxy = requests.get(
        'https://gimmeproxy.com/api/getProxy?country=RU&get=true&supportsHttps=true&protocol=http')
    proxy_json = json.loads(proxy.content)
    if proxy.status_code != 200 and 'ip' not in proxy_json:
        raise RequestException
    else:
        return proxy_json['ip'] + ':' + proxy_json['port']


proxy_env = os.environ.get('AVITO_PROXY_HTTP')
if proxy_env:
    if proxy_env == "auto":
        proxy_list = [get_proxy()]
    else:
        proxy_list = os.environ.get('AVITO_PROXY_HTTP').split(",")
else:
    proxy_list = None


def get_html(url, proxy=None):
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
    if proxy_list:
        proxies = {
            'http': 'http://' + proxy,
            'https': 'https://' + proxy,
        }
        response = requests.get(url, headers=headers, proxies=proxies, timeout=Config.REQUEST_TIMEOUT)
    else:
        response = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
    return response.content


def get_ads_list(avito_search_url, log=None):
    """
    :param avito_search_url: url like https://m.avito.ru/kazan/avtomobili/inomarki?pmax=200000&pmin=50000
    :return: ads list
    """
    if proxy_list:
        proxy = random.choice(proxy_list)
    else:
        proxy = None
    try:
        html = get_html(avito_search_url, proxy)
    except BaseException as be:
        if log:
            log.error(f"{proxy}, {be}")
        return
    # f = open("avito-1.html", "r")
    # html = f.read()

    soup = BeautifulSoup(html, 'lxml')

    f = open(Config.TEMP + "/avito-test.html", "w+")
    f.write(soup.prettify())
    f.close()

    print(f'html lenght {len(soup.prettify())}')

    ads = soup.select('.item.item_table')
    if log and not ads:
        log.warn(f"no ads with proxy {proxy}")
    print(f'ads count {len(ads)}')
    timestamp = int(time.time())
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
            price = price_span.text.strip()
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
                'created': created,
                'parsed': timestamp,
                'url': url,
                'img': img_url,
            })
    return ads_list


def get_new_ads(new, old):
    _ = []
    old_links = [l['url'] for l in old]
    for ad in new:
        if ad['url'] not in old_links:
            _.append(ad)
    return _


if __name__ == '__main__':
    get_ads_list('https://www.avito.ru/kazan/igry_pristavki_i_programmy/igrovye_pristavki-ASgBAgICAUSSAsoJ?q=ps4+pro')
