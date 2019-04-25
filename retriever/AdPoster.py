import scrapy
import os
from scrapy.item import Item
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


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
        description = response.xpath('//div[@itemprop="description"]/p/text()').getall()
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

def GetData(URL):
    process = CrawlerProcess(get_project_settings())
    process.crawl(DataRetriever, URL=URL)
    process.start() # the script will block here until the crawling is finished

if __name__ == "__main__":
    URL = raw_input("Enter URL\n")
    GetData(URL)
