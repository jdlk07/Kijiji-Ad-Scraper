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
from billiard import Process
from twisted.internet import reactor
import threading
import json
from datetime import datetime
import time
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class ImgData(Item):
#Required to retrieve images via scrapy.
    image_urls=scrapy.Field()
    images=scrapy.Field()
    image_name=scrapy.Field()

class DataRetriever(scrapy.Spider):
#The scrapy spider. Crawls URL or list of URL's for the following information: Title, Description, Address, Price, Images. Save this information in an "ads" folder under the ad reference number.
    name = "data"
    # def __init__(self, url):
    #     self.url = url
    # def __init__(self):
        # chrome_options = Options()
        #chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--headless")
        # self.driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)

    def start_requests(self):
        print "Requesting URL"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        url = response.url
        ref_num = getRefNum(url)
        ad_dir = "ref_" + ref_num
        title = response.xpath('//div[@itemprop="Product"]//h1[@itemprop="name"]/text()').get()
        if title == None:
            print "Invalid URL. Script will exit."
            sys.exit()
        description = response.xpath('//div[@itemprop="description"]//p/text()').getall()
        address = response.xpath('//span[@itemprop="address"]/text()').get()
        price = response.xpath('//span[@itemprop="price"]/text()').get()
        path = response.xpath('//span[@itemprop="name"]/text()').getall()
        state = path[0]
        area = path[1]
        city = path[2]
        category = path[-3]
        subCategory = path[-2]
        subSubCategory = path[-1].split(" in ")[0]
        # tel = response.xpath('//a[starts-with(@href,"tel:")]/span/span/text()').extract_first()
        image_urls = response.xpath('//img[@itemprop="image"]/@src').extract()
        # image_urls = ['https://i.ebayimg.com/00/s/NjAwWDgwMA==/z/OCgAAOSwiolcw1i-/$_59.JPG']
        title_filename = 'ads/%s/title.text' %ad_dir
        description_filename = 'ads/%s/description.text' %ad_dir
        address_filename = 'ads/%s/address.text' %ad_dir
        price_filename = 'ads/%s/price.text' %ad_dir
        url_filename = 'ads/%s/old_url.text' %ad_dir
        json_filename = 'ads/%s/details.json' %ad_dir
        details = {"title": title,
            "description": description,
            "address": address,
            "price": price,
            "category": category,
            "subCategory": subCategory,
            "subSubCategory": subSubCategory,
            "state": state,
            "area": area,
            "city": city,
            "oldUrl": url,
            "newUrl": ""}
        print "Now downloading %s "%title
        if not os.path.exists('ads/' + ad_dir):
            os.mkdir('ads/' + ad_dir)
        with open(json_filename, 'w') as jsonFile:
            json.dump(details, jsonFile)
            print "Wrote details json file"
        with open(title_filename, 'w+') as titleFile:
            titleFile.write(title.encode('utf-8'))
            print "Wrote title text file"
        with open(description_filename, 'w+') as descriptionFile:
            for paragraph in description:
                descriptionFile.write(paragraph.encode('utf-8') + "\n")
            print "Wrote description text file"
        with open(address_filename, 'w+') as addressFile:
            addressFile.write(address.encode('utf-8'))
            print "Wrote address text file"
        with open(price_filename, 'w+') as priceFile:
            priceFile.write(price.encode('utf-8'))
            print "Wrote price text file"
        with open(url_filename, 'w+') as urlFile:
            urlFile.write(url.encode('utf-8'))
            print "Wrote old url text file"
        yield ImgData(image_urls=image_urls, image_name="%s/images/image" %ad_dir)

def getRefNum(url):
    if "adId=" in url:
        ref_num = url.split("adId=")[-1]
        if "&" in ref_num:
            ref_num = ref_num.split("&")[0]
    else:
        ref_num = url.split("/")[-1].split("?")[0]
    return ref_num

def getUrls():
    url_list = []
    with open('urls.text') as file:
        counter = 1
        for line in file:
            line = line.rstrip()
            if counter == 1:
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

def runSpider(url):
#Custom function to run spider multiple times within the same twisted reactor as the twisted reactor can only be started once however the spider can be run multiple times within the same reactor.
    print "Spider Called"
    def f(q):
        try:
            runner = crawler.CrawlerRunner(get_project_settings())
            deferred = runner.crawl(DataRetriever, url=url)
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

def getState(data):
    state = data['state']
    if state == "Ontario":
        area = data['area']
        if area[0] <= "L":
            state = state + " (A - L)"
        else:
            state = state + " (M - Z)"
    else:
        state = state
    return state

def waitForElem(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except Exception:
        print "The element timed out before it passed the WebDriverWait test..."

def click(driver, xpath):
    waitForElem(driver, xpath)
    driver.find_element_by_xpath(xpath).click()

def waitPageLoad(driver, old_url):
    counter = 0
    print "Next page has not loaded yet",
    while True:
        new_url = driver.current_url
        if old_url != new_url:
            print "\nNext Page has loaded."
            break
        else:
            sys.stdout.write(".")
            sys.stdout.flush()

def signIn(driver, username, password, sign_in_url):
    old_url = sign_in_url
    counter = 0
    print "Signing In",
    while True:
        try:
            driver.find_element_by_id('LoginEmailOrNickname').send_keys(username)
            driver.find_element_by_id('login-password').send_keys(password)
            signInBtnXpath = '//button[@id="SignInButton"]'
            click(driver, signInBtnXpath)
            print "\nSigned in successfuly"
            break
        except NoSuchElementException:
            sys.stdout.write(".")
            sys.stdout.flush()

    waitPageLoad(driver, old_url)

def useSearchById(driver, url):
    old_url = driver.current_url
    ref_num = getRefNum(url)
    searchInputXpath = '//input[@id="SearchKeyword"]'
    print "Trying to enter search input",
    while True:
        try:
            driver.find_element_by_xpath(searchInputXpath).clear()
            driver.find_element_by_xpath(searchInputXpath).send_keys(ref_num)
            print "\nSearch input was sent " + str(ref_num)
            break
        except Exception as e:
            print e
            sys.stdout.write(".")
            sys.stdout.flush()
    searchBtnXpath = '//button[@name="SearchSubmit"]'
    while True:
        try:
            click(driver, searchBtnXpath)
            print "Search button was clicked"
            break
        except Exception:
            print "Search button could not be clicked. Trying again..."
    waitPageLoad(driver, old_url)

def deleteAd(driver, url):
    useSearchById(driver, url)
    current_url = driver.current_url
    while True:
        deleteBtnXpath = '//div[@class="ad-actions"]//a[normalize-space(text())=("Delete")]'
        try:
            print "Attempting Delete Button Click"
            click(driver, deleteBtnXpath)
            print "Delete button was clicked"
            break
        except Exception:
            print "Delete button could not be clicked. Trying again..."
    waitPageLoad(driver, current_url)

def insertLocation(driver, data):
    state = getState(data)
    area = data['area']
    stateBtnXpath = '//ul[@class="locMenu drop-down level-1"]//a[normalize-space(text())="' + state + '"]'
    click(driver, stateBtnXpath)
    areaBtnXpath = '//ul[@class="locMenu drop-down level-2"]//a[normalize-space(text())="' + area + '"]'
    click(driver, areaBtnXpath)
    driver.find_element_by_xpath('//a[normalize-space(text())="Go"]').click()
    print "Location was selected"

def insertTitle(driver, data):
    title = data['title']
    AdTitleFormXpath = '//textarea[@id="AdTitleForm"]'
    element = waitForElem(driver, AdTitleFormXpath)
    driver.find_element_by_xpath(AdTitleFormXpath).send_keys(title)
    driver.find_element_by_xpath('//button[normalize-space(text())="Next"]').click()
    print "Title was inserted"

def insertCategory(driver, data):
    category = data['category']
    while True:
        try:
            categoryBtnXpath = '//button[h5[normalize-space(text())="' + category +'"]]'
            click(driver, categoryBtnXpath)
            print "Category was clicked"
            break
        except Exception:
            print "Category was not found. Refreshing page and trying again..."
            # element = raw_input("enter anything to continue ")
            driver.refresh()
            insertTitle(driver, data)

def insertSubCategory(driver, data):
    subCategory = data['subCategory']
    while True:
        try:
            subCategoryBtnXpath = '//button[h5[normalize-space(text())="' + subCategory +'"]]'
            click(driver, subCategoryBtnXpath)
            print "Sub Category was clicked"
            break
        except Exception:
            print "Sub Category was not found. Clicking Category again and trying..."
            # element = raw_input("enter anything to continue ")
            insertCategory(driver, data)

def insertSubSubCategory(driver, data):
    subSubCategory = data['subSubCategory'].split(" in ")[0]
    while True:
        try:
            subSubCategoryBtnXpath = '//button[h5[normalize-space(text())="' + subSubCategory +'"]]'
            click(driver, subSubCategoryBtnXpath)
            print "Sub Sub Category was clicked"
            break
        except Exception:
            print "The sub sub category could not be clicked. Trying again..."
            driver.refresh()
            insertTitle(driver, data)
            insertCategory(driver, data)
            insertSubCategory(driver, data)

def insertCategories(driver, data):
    current_url = driver.current_url
    insertCategory(driver, data)
    insertSubCategory(driver, data)
    insertSubSubCategory(driver, data)
    print "Categories section complete"
    waitPageLoad(driver, current_url)

def checkTitle(driver, data):
    title = data['title']
    titleInputXpath = '//input[@id="postad-title"]'
    while True:
        try:
            titleInput = driver.find_element_by_xpath(titleInputXpath)
            break
        except Exception:
            print "Title Input could not be found. Trying again..."
    if len(titleInput.get_attribute('value')) < 1:
        titleInput.send_keys(title)
        print "Title was not inserted in details page. Inserted now."
    else:
        print "Title already inserted in details page"

def insertAddress(driver, data):
# function must be the first to run on this page as if the address autocomplete does NOT populate, the page is refreshed
    address = data['address']
    postal_code = address[-7:]
    while True:
        try:
            driver.find_element_by_xpath('//textarea[@id="location"]').send_keys(postal_code)
        except Exception:
            print "Address Entry field was not found. Clicking Change button instead and then adding address..."
            locationChangeBtn = '//div[@data-fes-id="locationModule"]//button[normalize-space(text())="Change"]'
            click(driver, locationChangeBtn)
            driver.find_element_by_xpath('//textarea[@id="location"]').send_keys(postal_code)
            print "Address was inserted"
        try:
            time.sleep(3)
            addressSelectBtnXpath = '//textarea[@id="location"]/../../../following-sibling::div/div[1]'
            click(driver, addressSelectBtnXpath)
            print "The address suggestion was found and clicked."
            break
        except Exception:
            print "There was no address suggestion to click. Refreshing page and trying again..."
            driver.refresh()

def insertPrice(driver, data):
    price = data['price']
    if not price:
        driver.find_element_by_xpath('//label[@for="priceType2"]').click()
        print "No price listed. The 'Contact' option was selected instead"
    else:
        price = price.replace("$", "")
        priceInputXpath = '//input[@id="PriceAmount"]'
        driver.find_element_by_xpath(priceInputXpath).send_keys(price)
        print "The price was inserted."

def submitAd(driver):
    submit_page_url = driver.current_url
    print "Trying to click submit button"
    while True:
        try:
            driver.find_element_by_xpath('//button[@name="saveAndCheckout"]').click()
            print "The submit button was clicked"
            break
        except Exception:
            sys.stdout.write(".")
            sys.stdout.flush()
    waitPageLoad(driver, submit_page_url)

def getNewUrl(driver):
    post_submission_url = driver.current_url
    useSearchById(driver, post_submission_url)
    new_url = driver.current_url
    new_url = new_url.split("?")[0]
    print "The new url is " + new_url
    return new_url


def saveNewUrl(ref_num, new_url, data):
    jsonFileName = 'ads/ref_%s/details.json'%ref_num
    data['newUrl'] = new_url
    with open(jsonFileName, "w") as jsonFile:
        json.dump(data, jsonFile)
    print "The new URL was saved into the json file"

    url_filename = 'ads/ref_%s/new_url.text' %ref_num
    with open(url_filename, 'w+') as urlFile:
        urlFile.write(new_url.encode('utf-8'))
        print "Wrote new url text file"

def DeleteAndUpload(username, password, url):
    ref_num = getRefNum(url)
    jsonFileName = 'ads/ref_%s/details.json'%ref_num
    try:
        with open(jsonFileName, "r") as jsonFile:
            data = json.load(jsonFile)
    except IOError:
        print "Exiting script..."
        sys.exit()
    description = data['description']
    imagePath = os.getcwd() + "ads/%s/images/image1.jpg"%ref_num
    print "Now Uploading " + data['title']
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)
    caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "normal"  #  complete
    # caps["pageLoadStrategy"] = "eager"  #  interactive. Not Working on Chrome
    caps["pageLoadStrategy"] = "none"
    driver = webdriver.Chrome('./chromedriver', desired_capabilities=caps, chrome_options=chrome_options)
    start_url = 'https://www.kijiji.ca/t-login.html'
    driver.get(start_url)
    signIn(driver, username, password, start_url)

    deleteAd(driver, url)
    # insertLocation(driver, data)

    postAdBtnXpath = '//a[@title="Post ad"]'
    click(driver, postAdBtnXpath)

    insertTitle(driver, data)

    insertCategories(driver, data)

# Below function must be the first to run on this page as if the address autocomplete does NOT populate, the page is refreshed
    insertAddress(driver, data)

    checkTitle(driver, data)

    driver.find_element_by_xpath('//textarea[@id="pstad-descrptn"]').send_keys(description)

    insertPrice(driver, data)

    submitAd(driver)

    new_url = getNewUrl(driver)

    saveNewUrl(ref_num, new_url, data)

if __name__ == "__main__":
    url_list = getUrls()
    username = raw_input("Enter Kijiji Username:\n")
    password = raw_input("Enter Kijiji Password:\n")
    for item in url_list:
        url = item['url']
        ref_num = getRefNum(url)
        startTime = item['startTime']
        startTime = datetime.strptime(startTime,"%H:%M").time()
        endTime = item['endTime']
        endTime = datetime.strptime(endTime,"%H:%M").time()
        interval = item['interval']
        while True:
            currentTime = datetime.now().time()
            if currentTime > startTime and currentTime < endTime:
                print "ready to go"
                runSpider(url)
                break
            else:
                print "waiting"
        DeleteAndUpload(username, password, url)

        print ref_num + " has finished uploading"
        print "Sleeping for %s"%interval
        time.sleep(interval)
    print "crawl complete"
