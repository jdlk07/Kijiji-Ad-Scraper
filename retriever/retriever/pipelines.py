# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os, os.path
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request


class CustomImageNamePipeline(ImagesPipeline):
    # def get_media_requests(self, item, info):
    #     return [Request(x, meta={'image_name': item["image_name"]})
    #             for x in item.get('image_urls', [])]

    def get_media_requests(self, item, info):
        for i, image_url in enumerate(item.get('image_urls', [])):
            yield Request(image_url, meta={'image_name': item['image_name'] + str(i)})

    def file_path(self, request, response=None, info=None):
        return '%s.jpg' % request.meta['image_name']

        
class RetrieverPipeline(object):
    def process_item(self, item, spider):
        return item

