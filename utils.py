def check_avito_url(avito_url):
    from urllib.parse import urlparse
    url_parts = urlparse(avito_url)
    return url_parts.netloc.endswith('avito.ru') and len(url_parts.path) > 1


def get_img_file_by_url(url):
    from fake_useragent import UserAgent
    import requests
    ua = UserAgent()

    if url[:2] == '//':
        url = url.replace('//', 'https://')

    try:
        file = requests.get(url=url, headers={
            'User-Agent': ua.random
        }).content
        return file
    except:
        return None
