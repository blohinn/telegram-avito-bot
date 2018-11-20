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
        'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv)',
        'Chrome/70.0.3538.77 Safari/537.36',
        'Opera/9.68 (X11; Linux i686; en-US) Presto/2.9.344 Version/11.00',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows 95; Trident/5.1)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_6) AppleWebKit/5342 (KHTML, like Gecko) Chrome/37.0.896.0 Mobile Safari/5342',
        'Mozilla/5.0 (Windows; U; Windows NT 6.2) AppleWebKit/533.49.2 (KHTML, like Gecko) Version/5.0 Safari/533.49.2',
        'Mozilla/5.0 (Windows NT 5.0; sl-SI; rv:1.9.2.20) Gecko/20110831 Firefox/37.0'
    ]
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    proxy = {
        # 'https': get_proxy()
    }
    response = requests.get(url, headers=headers)
    return response.content


def get_ads_list(avito_search_url):
    """
    :param avito_search_url: url like https://m.avito.ru/kazan/avtomobili/inomarki?pmax=200000&pmin=50000
    :return: ads list
    """
    html = get_html(avito_search_url)
    soup = BeautifulSoup(html, 'lxml')
    ads = soup.find_all('article', {'class': 'b-item'})

    ads_list = []
    for ad in ads:
        ad_wrapper = ad.find('div', {'class': 'b-item-wrapper'})
        ad_wrapper_a = ad_wrapper.find('a')

        ad_id = ad.attrs['data-item-id']
        ad_url = 'https://m.avito.ru' + ad_wrapper_a.attrs['href']
        ad_header = ad_wrapper_a.find('h3').text

        ad_price = ad_wrapper_a.find('div', {'class': 'item-price'})
        ad_price = ad_price.find('span').text

        ad_img = ad_wrapper_a.find('div', {'class': 'item-img'})
        ad_img_span = ad_img.find('span')

        if ad_img_span:
            ad_img = ad_img_span.attrs['style']
            ad_img = ad_img.split(' ')[1]
            ad_img = 'https://' + ad_img[6:-2]
        else:
            ad_img = None

        is_ad_premium = 'item-vip' in ad.attrs['class']
        is_ad_highlight = 'item-highlight' in ad.attrs['class']

        # print("%-70s %-15s %-15s" % (ad_header, ad_price, ad_id))
        if not is_ad_premium and not is_ad_highlight:
            ads_list.append({
                'id': ad_id,
                'title': ad_header.replace(u'\xa0', u' '),
                'price': ad_price.replace(u'\xa0', u' '),
                'url': ad_url,
                'img': ad_img
            })

    return ads_list


def get_new_ads(new, old):
    _ = []
    for ad in new:
        if ad not in old:
            _.append(ad)
    return _
