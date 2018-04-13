##
## Crawls apks from https://www.androiddrawer.com/
##

import scrapy
import os
import logging
from datetime import datetime


class ApkSpider(scrapy.Spider):
    name = 'apk_spider'
    start_urls = ['https://www.androiddrawer.com/']

    # Setup logger
    logger = logging.getLogger('crawl-logger')
    formatter = logging.Formatter('%(levelname)-5s  [%(asctime)s]  %(message)s')
    fileHandler = logging.FileHandler('apkcrawler_' + datetime.now().strftime("%Y_%m_%d__%H_%M_%S") + '.log', mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    logger.info('Starting to crawl...')

    if os.path.exists('apks') is False:
        os.mkdir('apks')
    os.chdir('apks')

    # Parses the whole category list
    def parse(self, response):
        for category in response.css('#categoriesContainer li'):
            category_href = category.css('a ::attr(href)').extract_first()
            if category_href:
                request = scrapy.Request(
                    url=response.urljoin(category_href),
                    callback=self.parse_category
                )
                foldername = category.css('a ::text').extract_first()
                request.meta['foldername'] = foldername
                yield request

    # Parses one category
    def parse_category(self, response):
        for app in response.css('a.box-click-target.animate'):
            app_href = app.css('a ::attr(href)').extract_first()
            if app_href:
                yield scrapy.Request(
                    url=response.urljoin(app_href),
                    callback=self.parse_app,
                    meta=response.meta
                )

    # Parses app page
    def parse_app(self, response):
        download_btn = response.css('a.download-btn.animate')
        size = download_btn.css('.download-size ::text').extract_first()
        size = int(float(size[:-3]))
        if size <= 50:
            href = download_btn.css('a ::attr(href)').extract_first()
            request = scrapy.Request(
                url=response.urljoin(href),
                callback=self.save_apk,
                meta=response.meta
            )
            filename = response.css('h1.entry-title.single-title ::text').extract_first()
            request.meta['filename'] = filename
            yield request

    # Saves .apk to the category folder
    def save_apk(self, response):
        logger = logging.getLogger('crawl-logger')

        foldername = response.meta['foldername']
        filename = response.meta['filename'].replace(':', ' ') + '.apk'
        path = os.path.join(foldername, filename)

        if len(response.body) // (1 << 20) == 0 or len(response.body) == 0:
            logger.debug("Couldn't download {} correctly :( Length: {}".format(path, len(response.body)))
            return

        if os.path.exists(foldername) is False:
            os.mkdir(foldername)

        with open(path, 'wb') as f:
            f.write(response.body)

        logger.info(path + ' Length: ' + str(len(response.body)))
