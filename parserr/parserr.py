import json
import requests
import time
from bs4 import BeautifulSoup
from requests import RequestException


def get_proxy():
    proxy = requests.get('https://gimmeproxy.com/api/getProxy?country=RU&get=true&supportsHttps=true&protocol=http')
    proxy_json = json.loads(proxy.content)
    if proxy.status_code != 200 and 'ip' not in proxy_json:
        raise RequestException
    else:
        return 'http://' + proxy_json['ip'] + ':' + proxy_json['port']


def get_html(url):
    from fake_useragent import UserAgent
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random
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
