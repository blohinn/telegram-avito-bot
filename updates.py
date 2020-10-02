import time

import db
from main import bot
from parserr.parserr import get_ads_list, get_new_ads

MSG = "{0}: {1}\n{2}\n{3}\n{4}"


def send_updates():
    print("start handling updates")
    sce = db.get_search_collection_entries()

    for i in sce:
        tracking_urls = []
        for url in i['tracking_urls']:
            old_ads = url['ads']
            print(url['name'])
            actual_ads = get_ads_list(url['url'])
            while not actual_ads:
                time.sleep(5)
                actual_ads = get_ads_list(url['url'])
            print(f'parsed ads count = {len(actual_ads)}')
            new_ads = get_new_ads(actual_ads, old_ads)
            print(f'new_ads count = {len(new_ads)}')

            for n_a in new_ads:
                msg = MSG.format(url['name'], n_a['title'].rstrip(), n_a['price'].rstrip(), n_a['created'].rstrip(),
                                 n_a['url'])

                # if n_a['img']:
                #     from utils import get_img_file_by_url
                #
                #     img_file = get_img_file_by_url(n_a['img'])
                #     if img_file:
                #         bot.send_photo(i['uid'], img_file)

                bot.send_message(i['uid'], msg)

            url['ads'] = actual_ads
            tracking_urls.append(url)

            import random
            time.sleep(random.randint(1, 15) / 10)
        db.set_actual_ads(i['uid'], tracking_urls)


if __name__ == '__main__':
    import schedule

    send_updates()
    schedule.every(2).minutes.do(send_updates)

    while True:
        schedule.run_pending()
        time.sleep(1)
