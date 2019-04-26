import scrapy
import os
from scrapy.item import Item
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerRunner
import scrapy.crawler as crawler
from scrapy.utils.project import get_project_settings
from multiprocessing import Process, Queue
from twisted.internet import reactor
import threading
import json
# import sqlite3
# from sqlite3 import Error
# from db_utils import db_connect

# def create_connection(db_file):
#     """ create a database connection to a SQLite database """
#     try:
#         conn = sqlite3.connect(db_file)
#         print(sqlite3.version)
#     except Error as e:
#         print(e)
#     finally:
#         conn.close()
#
# def create_table():
#      con = db_connect() # connect to the database
#      cur = con.cursor() # instantiate a cursor obj
#      url_table = """CREATE TABLE IF NOT EXISTS url_list (
#         id integer PRIMARY KEY,
#         url text NOT NULL,
#         start integer NOT NULL,
#         end integer NOT NULL,
#         interval integer NOT NULL)"""
#     CREATE TABLE IF NOT EXISTS url_table (
#     id integer PRIMARY KEY,
#     name text NOT NULL,
#     begin_date text,
#     end_date text
#     );
#     cur.execute(url_table)

class ImgData(Item):
#Required to retrieve images via scrapy.
    image_urls=scrapy.Field()
    images=scrapy.Field()
    image_name=scrapy.Field()

class DataRetriever(scrapy.Spider):
#The scrapy spider. Crawls URL or list of URL's for the following information: Title, Description, Address, Price, Images. Save this information in an "ads" folder under the ad reference number.
    name = "data"

    # def __init__(self):
        # chrome_options = Options()
        #chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--headless")
        # self.driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)

    def start_requests(self):
        # urls = [
        #     'https://www.kijiji.ca/v-bed-mattress/mississauga-peel-region/brand-new-queen-size-pillow-top-mat-box-both-for-249/1324601512',
        #     'https://www.kijiji.ca/v-bed-mattress/city-of-toronto/wholesale-furniture-warehouse-we-beat-any-price-lowest-price-guaranteed-www-aerys-ca/c3770284',
        #     'https://www.kijiji.ca/v-camera-camcorder-lens/city-of-toronto/dji-ronin-m-w-nanuk-940-hardcase/1429494111'
        # ]
        urls = [URL]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # self.driver.get(response.url)
        # self.driver.close()
        ref_num = response.url.split("/")[-1].split("?")[0]
        title = response.xpath('//h1[@itemprop="name"]/text()').get()
        description = response.xpath('//div[@itemprop="description"]//p/text()').getall()
        address = response.xpath('//span[@itemprop="address"]/text()').get()
        price = response.xpath('//span[@itemprop="price"]/text()').get()
        # tel = response.xpath('//a[starts-with(@href,"tel:")]/span/span/text()').extract_first()
        image_urls = response.xpath('//img[@itemprop="image"]/@src').extract()
        title_filename = 'ads/%s/title.text' %ref_num
        description_filename = 'ads/%s/description.text' %ref_num
        address_filename = 'ads/%s/address.text' %ref_num
        price_filename = 'ads/%s/price.text' %ref_num
        tel_filename = 'ads/%s/tel.text' %ref_num
        if not os.path.exists('ads/' + ref_num):
            os.mkdir('ads/' + ref_num)
        with open(title_filename, 'wb') as titleFile:
            titleFile.write(title.encode('utf-8'))
        with open(description_filename, 'wb') as descriptionFile:
            for paragraph in description:
                descriptionFile.write(paragraph.encode('utf-8') + "\n")
        with open(address_filename, 'wb') as addressFile:
            addressFile.write(address.encode('utf-8'))
        with open(price_filename, 'wb') as priceFile:
            priceFile.write(price.encode('utf-8'))
        yield ImgData(image_urls=image_urls, image_name="%s/images/image" %ref_num)

# def GetData(URL):
#     process = CrawlerProcess(get_project_settings())
#     process.crawl(DataRetriever, URL=URL)
#     process.start() # the script will block here until the crawling is finished

def getUrls():
    url_list = []
    with open('urls.text') as file:
        counter = 1
        for line in file:
            line.rstrip('\n')
            if counter == 1:
                line = line.split("?")[0]
                url = line
            elif counter == 2:
                startTime = line
            elif counter == 3:
                endTime = line
            elif counter == 4:
                interval = line
                newAd = {
                    "url": url,
                    "startTime": startTime,
                    "endTime": endTime,
                    "interval": interval
                    }
                url_list.append(newAd)
            elif counter == 5:
                counter = 0
            counter += 1
    return url_list

def runSpider(spider, URL):
#Custom function to run spider multiple times within the same twisted reactor as the twisted reactor can only be started once however the spider can be run multiple times within the same reactor.
    print("spider running")
    def f(q):
        try:
            runner = crawler.CrawlerRunner(get_project_settings())
            deferred = runner.crawl(spider)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result

def runSpiderLoop(DataRetriever):
    while True:
        while len(url_list) > 0:
            print(url_list)
            for url in url_list:
                print("calling spider on url in list")
                runSpider(DataRetriever, url)

# def getInput():
#     while True:
#         URL = raw_input("Enter URL Below:\n")
#         startTime = raw_input("Enter Start Time as HHMM\n")
#         endTime = raw_input("Enter End Time as HHMM\n")
#         pauseTime = raw_input("Enter Time to Wait\n")
#         ref_num = URL.split("/")[-1].split("?")[0]
#         newAd = {
#             "url": URL,
#             "startTime": startTime,
#             "endTime": endTime,
#             "pauseTime": pauseTime
#         }
#         with open('urls/'+ ref_num +'.json', 'w') as outfile:
#             json.dump(newAd, outfile)
#
# if not os.path.exists('urls/'):
#     os.mkdir('urls/')
# try:
#     with open('urls/urls.json') as jsonFile:
#         url_list = json.load(jsonFile)
# except IOError:
#     print("No json file found. Will create new file on url entry")
#     url_list = []

if __name__ == "__main__":
    print getUrls()

    # getInputThread = threading.Thread(target=getInput)
    # getInputThread.start()
    # spiderThread = threading.Thread(target=runSpiderLoop, args=(DataRetriever,))
    # spiderThread.start()
    # while True:
    #     URL = raw_input("Enter URL Below:\n")
    #     runSpider(DataRetriever, URL)
