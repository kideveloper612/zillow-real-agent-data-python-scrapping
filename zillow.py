import requests
import argparse
import json
import re
from bs4 import BeautifulSoup

realtors = []
past_sales = []
def location_code(hint):
    URL = 'https://ac.zillowstatic.com/getRegionByPrefix?prefix=%s&json&callback=YUI.Env.JSONP.zillowSearchAutoComplete' % hint
    response = requests.get(url=URL).text
    json_data = json.loads(response.replace('YUI.Env.JSONP.zillowSearchAutoComplete(', '').replace(')', ''))
    return json_data

def argument_parse():
    parser = argparse.ArgumentParser(description='Hint for location!')
    parser.add_argument("location", type=str, nargs='+')
    args = parser.parse_args()
    location = args.location
    return location

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
    print(line)
    return line

def get_sale(page, data_id):
    url = 'https://www.zillow.com/ajax/profile-sales-history/?p=%s&zuid=%s' % (page, data_id)
    res = requests.request('GET', url=url).text
    tx = json.loads(res)['tx']
    if not tx:
        return past_sales
    for t in tx:
        image = t['image']
        address = t['fullAddress']
        represented = t['represented']
        price = t['price']
        bed = t['bed']
        date = t['date']
        line = [image, address, represented, price, bed, date]
        past_sales.append(line)
    return get_sale(page=page+1, data_id=data_id)

def beautiful_soup(link):
    profileLink_soup = BeautifulSoup(requests.get(url=link).content, 'lxml')
    print(profileLink_soup)
    print(profileLink_soup.find('div', {'class': 'ctcd-contact-card-inner'}))
    data_id = profileLink_soup.find('a', {'class': 'ctcd-contact-card-inner'})['data-zuid']
    return get_sale(page=1, data_id=data_id)

def get_location(page):
    location = argument_parse()
    if re.match(r'^-?\d+(?:\.\d+)?$', location[0]) is None:
        location = ' '.join(location)
        url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=%s&locationText=%s' % (page, location)
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        }
        response = requests.request("GET", url, headers=headers)
        parse = json.loads(response.text)['model']['viewModel']['boards']
        if not parse['boards']:
            return realtors
        for board in parse['boards']:
            profileLink = 'https://www.zillow.com' + board['href']
            sales = beautiful_soup(profileLink)
            print(sales)
            exit()
            line = json_parse(board=board)
            realtors.append(line)
        return get_location(page+1)

    else:
        url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=page&locationText=%s' % (page, location[0])
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        }
        response = requests.request("GET", url, headers=headers)
        parse = json.loads(response.text)['model']['viewModel']['boards']
        if parse['boards'] == 'None':
            return realtors
        for board in parse['boards']:
            profileLink = 'https://www.zillow.com' + board['href']
            sales = beautiful_soup(link=profileLink)
            line = json_parse(board=board)
            realtors.append(line)
        return get_location(page+1)

# realtors = get_location(1)
print(realtors)

print(requests.get(url='https://www.zillow.com/profile/MichaelNapolitanoJr/').text)