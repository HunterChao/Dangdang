# -*- coding: utf-8 -*-
import scrapy
import requests
from scrapy import Selector
from lxml import etree
from ..items import DangdangItem
from scrapy_redis.spiders import RedisSpider

class DangdangSpider(RedisSpider):
    name = 'dangdangspider'
    redis_key = 'dangdangspider:urls'
    allowed_domains = ["dangdang.com"]
    start_urls = 'http://category.dangdang.com/cp01.00.00.00.00.00.html'

    def start_requests(self):
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 \
                      Safari/537.36 SE 2.X MetaSr 1.0'
        headers = {'User-Agent': user_agent}
        yield scrapy.Request(url=self.start_urls, headers=headers, method='GET', callback=self.parse)

    def parse(self, response):
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 \
                      Safari/537.36 SE 2.X MetaSr 1.0'
        headers = {'User-Agent': user_agent}
        lists = response.body.decode('gbk')
        selector =  etree.HTML(lists)
        goodslist = selector.xpath('//*[@id="leftCate"]/ul/li')
        for goods in goodslist:
            try:
                category_big = goods.xpath('a/text()').pop().replace('   ','')  # 大种类
                category_big_id = goods.xpath('a/@href').pop().split('.')[1]    # id
                category_big_url = "http://category.dangdang.com/pg1-cp01.{}.00.00.00.00.html".\
                                  format(str(category_big_id))
                yield scrapy.Request(url=category_big_url, headers=headers,callback=self.detail_parse,
                                     meta={"ID1":category_big_id,"ID2":category_big})
            except Exception:
                pass


    def detail_parse(self, response):
        '''
        ID1:大种类ID   ID2:大种类名称   ID3:小种类ID  ID4:小种类名称
        '''
        url = 'http://category.dangdang.com/pg1-cp01.{}.00.00.00.00.html'.format(response.meta["ID1"])
        category_small = requests.get(url)
        contents = etree.HTML(category_small.content.decode('gbk'))
        goodslist = contents.xpath('//*[@class="sort_box"]/ul/li[1]/div/span')
        for goods in goodslist:
            try:
                category_small_name = goods.xpath('a/text()').pop().replace(" ","").split('(')[0]
                category_small_id = goods.xpath('a/@href').pop().split('.')[2]
                category_small_url = "http://category.dangdang.com/pg1-cp01.{}.{}.00.00.00.html".\
                                  format(str(response.meta["ID1"]),str(category_small_id))
                yield scrapy.Request(url=category_small_url, callback=self.third_parse, meta={"ID1":response.meta["ID1"],\
                       "ID2":response.meta["ID2"],"ID3":category_small_id,"ID4":category_small_name})
            except Exception:
                pass


    def third_parse(self,response):
        for i in range(1,101):
            url = 'http://category.dangdang.com/pg{}-cp01.{}.{}.00.00.00.html'.format(str(i),response.meta["ID1"],\
                                                                                      response.meta["ID3"])
            try:
                contents = requests.get(url)
                contents = etree.HTML(contents.content.decode('gbk'))
                goodslist = contents.xpath('//*[@class="list_aa listimg"]/li')
                for goods in goodslist:
                    item = DangdangItem()
                    try:
                        item['comments'] = goods.xpath('div/p[2]/a/text()').pop()
                        item['title'] = goods.xpath('div/p[1]/a/text()').pop()
                        item['time'] = goods.xpath('div/div/p[2]/text()').pop().replace("/", "")
                        item['price'] = goods.xpath('div/p[6]/span[1]/text()').pop()
                        item['discount'] = goods.xpath('div/p[6]/span[3]/text()').pop()
                        item['category1'] = response.meta["ID4"]       # 种类(小)
                        item['category2'] = response.meta["ID2"]       # 种类(大)
                    except Exception:
                        pass
                    yield item
            except Exception:
                pass

