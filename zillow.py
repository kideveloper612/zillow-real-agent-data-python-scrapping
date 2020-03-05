import requests
import argparse
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import os


lines = []
past_sales = []
csv_header = [['PHONE NUMBER', 'REPRESENTED', 'SOLD DATE', 'PRICE', 'REALTOR NAME', 'PHONE NUMBER', 'WEBSITE', 'SOCIAL1', 'SOCIAL2', 'SOCIAL3', 'SOCIAL4']]
def write_direct_csv(lines, filename):
    with open('output/%s' % filename, 'a', encoding="utf-8", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(lines)
    csv_file.close()

def write_csv(lines, filename):
    if not os.path.isdir('output'):
        os.mkdir('output')
    if not os.path.isfile('output/%s' % filename):
        write_direct_csv(lines=csv_header, filename=filename)
    write_direct_csv(lines=lines, filename=filename)

def json_parse(board):
    name, image, phone, totalReviewCount, reviewRating, reviewStars, listings, recentSales, review, excerpt, excerptDate = '', '', '', '', '', '', '', '', '', '', ''
    if board['contact']['summary']['profileLink']['text']:
        name = board['contact']['summary']['profileLink']['text']
    if board['contact']['graphic']['image']['src']:
        image = board['contact']['graphic']['image']['src']
    if board['contact']['summary']['phone']:
        phone = board['contact']['summary']['phone']
    if board['contact']['summary']['reviewLink']:
        totalReviewCount = board['contact']['summary']['reviewLink']['text']
    if board['contact']['summary']['reviewStars']['rating']:
        reviewRating = board['contact']['summary']['reviewStars']['rating']
    if board['contact']['summary']['reviewStars']['stars']:
        reviewStars = board['contact']['summary']['reviewStars']['stars']
    if board['map']['stats']['listings']:
        listings = board['map']['stats']['listings']
    if board['map']['stats']['recentSales']:
        recentSales = board['map']['stats']['recentSales']
    if board['map']['stats']['review']:
        review = board['map']['stats']['review']
    if board['reviewExcerpt']['excerpt']:
        excerpt = board['reviewExcerpt']['excerpt']
    if board['reviewExcerpt']['reviewLink']:
        excerptDate = board['reviewExcerpt']['reviewLink']['text']
    line = [name, image, phone, totalReviewCount, reviewRating, reviewStars, listings, recentSales, review, excerpt,
            excerptDate]
    return line

def location_code(hint):
    URL = 'https://ac.zillowstatic.com/getRegionByPrefix?prefix=%s&json&callback=YUI.Env.JSONP.zillowSearchAutoComplete' % hint
    response = requests.get(url=URL).text
    json_data = json.loads(response.replace('YUI.Env.JSONP.zillowSearchAutoComplete(', '').replace(')', ''))
    return json_data

def argument_parse():
    parser = argparse.ArgumentParser(description='Hint for location!')
    parser.add_argument("-l", "--location", type=str, nargs='+')
    parser.add_argument("-d", "--days", type=int)
    args = parser.parse_args()
    location = args.location
    days = args.days
    return location, days

def get_sale(page, data_id, day_count):
    if page == 1:
        past_sales = []
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
    }
    url = 'https://www.zillow.com/ajax/profile-sales-history/?p=%s&zuid=%s' % (page, data_id)
    res = requests.request('GET', url=url, headers=header).text
    tx = json.loads(res)['tx']
    if tx[0] is None:
        return past_sales
    for t in tx:
        if t is not None:
            d1 = datetime.strptime(t['date'], "%m/%d/%Y")
            d2 = datetime.strptime(str(datetime.today().strftime("%m/%d/%Y")), "%m/%d/%Y")
            if abs((d2 - d1).days) > int(day_count):
                return past_sales
            address, represented, price, date, = '', '', '', ''
            if 'fullAddress' in t:
                address = t['fullAddress']
            if 'represented' in t:
                represented = t['represented']
            if 'price' in t:
                price = t['price']
            if 'date' in t:
                date = t['date']
            line = [address, represented, date, price]
            past_sales.append(line)
    return get_sale(page=page+1, data_id=data_id, day_count=day_count)

def beautiful_soup(link, day_count):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
    }
    res = requests.request("GET", link, headers=headers)
    profileLink_soup = BeautifulSoup(res.content, 'lxml')
    data_id = profileLink_soup.find('a', {'class': 'show-lightbox zsg-button'})['data-zuid']
    socials = profileLink_soup.find('dd', {'class': 'profile-information-websites'})
    social_links = []
    if socials:
        socials_dom = socials.find_all('a')
        for social_dom in socials_dom:
            social_links.append(social_dom['href'])
    return get_sale(page=1, data_id=data_id, day_count=day_count), social_links

def get_location(page=1):
    location, day_count = argument_parse()
    if re.match(r'^-?\d+(?:\.\d+)?$', location[0]) is None:
        location = ' '.join(location)
        url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=%s&locationText=%s' % (page, location)
    else:
        url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=%s&locationText=%s' % (page, location[0])
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
    }
    response = requests.request("GET", url, headers=headers)
    parse = json.loads(response.text)['model']['viewModel']['boards']
    if not parse['boards']:
        return lines
    for board in parse['boards']:
        profileLink = 'https://www.zillow.com' + board['href']
        sales, links = beautiful_soup(profileLink, day_count)
        if sales:
            print(profileLink)
        line = json_parse(board=board)
        for sale in sales:
            tmp_line = [sale[0], sale[1], sale[2], sale[3], line[0], line[2]]
            for link in links:
                tmp_line.append(link)
            print(tmp_line)
            lines.append(tmp_line)
    return get_location(page+1)

records = get_location()
records.sort(key=lambda x: (datetime.strptime(x[2], '%m/%d/%Y'), x[0], x[1], x[3], x[4]), reverse=True)
write_csv(lines=records, filename='Zillow.csv')

