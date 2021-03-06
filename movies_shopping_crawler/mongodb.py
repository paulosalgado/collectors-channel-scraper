# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging as log
from pymongo import MongoClient

class MongoDbPipeline(object): 

    def __init__(self, url): 
        self.url = url

    @classmethod
    def from_crawler(cls, crawler): 
        return cls(
            url = crawler.settings.get('MONGO_URL')
        )

    def open_spider(self, spider): 
        self.client = MongoClient(self.url)
        db = self.client.movies
        self.col = db[spider.name]
        log.info('Opened MongoDB connection to <{}>'.format(spider.name))

    def close_spider(self, spider): 
        if self.client: 
            self.client.close()
            log.info('Closed MongoDB connection to <{}>'.format(spider.name))
        else: 
            log.info('MongoDB connection already closed to <{}>'.format(spider.name))

    def process_item(self, item, spider): 

        log.info('Processing in MongoDbPipeline item <{}>'.format(item))

        item_found = self.col.find_one({'url': item['url']})

        if item_found: 
            id_item_found = item_found.get('_id')
            item.update({'_id': id_item_found})
            self.col.update_one({'_id': id_item_found}, {'$set': dict(item)})
            log.info('Updated item with id <{}> using <{}>'.format(id_item_found, item))

            new_status = get_notification_status(item_found, item)

            if new_status and item['price'] != 'Indisponível': 
                item.update({'notification': new_status})
            else: 
                item.update({'notification': None})

        else: 
            id_item_new = self.col.insert_one(dict(item)).inserted_id
            item.update({'_id': id_item_new})
            log.info('Inserted item <{}> with id <{}>'.format(item, id_item_new))

            if item['price'] != 'Indisponível': 
                item.update({'notification': '🆕'})
            else: 
                item.update({'notification': None})
        
        return item


def get_notification_status(old, new): 

    old_price = old['price']
    new_price = new['price']

    try: 
        if float(new_price) < float(old_price): 
            old_price = old_price.replace('.', ',')
            return '⬇️ antes era R$ {}'.format(old_price)
        else: 
            return None
    except: 
        if old_price == 'Indisponível': 
            return '🔄 antes estava indisponível'
        elif new_price != old_price: 
            old_price = old_price.replace('.', ',')
            return '🔄 antes era R$ {}'.format(old_price)
        else: 
            return None        
