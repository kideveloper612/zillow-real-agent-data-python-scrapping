import requests
import argparse
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import os
import xlsxwriter

lines = []
# csv_header = [['PHONE NUMBER', 'REPRESENTED', 'SOLD DATE', 'PRICE', 'REALTOR NAME', 'PHONE NUMBER', 'BROKER ADDRESS',
#                'SCREEN NAME', 'MEMBER SINCE', 'WEBSITE', 'SOCIAL1', 'SOCIAL2',
#                'SOCIAL3', 'SOCIAL4']]




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


def argument_parse():
    parser = argparse.ArgumentParser(description='Hint for location!')
    parser.add_argument("-l", "--location", type=str, nargs='+')
    parser.add_argument("-d", "--days", type=int)
    args = parser.parse_args()
    location = args.location
    days = args.days
    return location, days


def location_code(hint):
    URL = 'https://ac.zillowstatic.com/getRegionByPrefix?prefix=%s&json&callback=YUI.Env.JSONP' \
          '.zillowSearchAutoComplete' % hint
    response = requests.get(url=URL).text
    json_data = json.loads(response.replace('YUI.Env.JSONP.zillowSearchAutoComplete(', '').replace(')', ''))
    return json_data


def write_direct_csv(d_lines, filename):
    with open('output/%s' % filename, 'a', encoding="utf-8", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(d_lines)
    csv_file.close()


class Z:
    def __init__(self):
        self.location, self.day_count = argument_parse()
        self.lines = []
        self.past_sales = []
        self.csv_header = [
            ['PHONE NUMBER', 'REPRESENTED', 'SOLD DATE', 'PRICE', 'REALTOR NAME', 'PHONE NUMBER', 'BROKER ADDRESS',
             'SCREEN NAME', 'MEMBER SINCE', 'WEBSITE', 'SOCIAL1', 'SOCIAL2',
             'SOCIAL3', 'SOCIAL4']]

    def write_csv(self, w_lines, filename):
        if not os.path.isdir('output'):
            os.mkdir('output')
        if not os.path.isfile('output/%s' % filename):
            write_direct_csv(d_lines=self.csv_header, filename=filename)
        write_direct_csv(d_lines=w_lines, filename=filename)

    def write_excel(self, e_lines):
        workbook = xlsxwriter.Workbook('output/Zillow.xlsx')
        worksheet = workbook.add_worksheet()
        col = 0
        for row, data in enumerate(e_lines):
            if row == 0:
                worksheet.write_row(row, col, self.csv_header[0])
            worksheet.write_row(row + 1, col, data)
        workbook.close()

    def get_sale(self, page, data_id):
        if page == 1:
            self.past_sales = []
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.122 Safari/537.36 '
        }
        url = 'https://www.zillow.com/ajax/profile-sales-history/?p=%s&zuid=%s' % (page, data_id)
        print(url)
        res = requests.request('GET', url=url, headers=header).text
        tx = json.loads(res)['tx']
        if tx[0] is None:
            return self.past_sales
        for t in tx:
            if t is not None:
                d1 = datetime.strptime(t['date'], "%m/%d/%Y")
                d2 = datetime.strptime(str(datetime.today().strftime("%m/%d/%Y")), "%m/%d/%Y")
                if abs((d2 - d1).days) > int(self.day_count):
                    return self.past_sales
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
                self.past_sales.append(line)
        return self.get_sale(page=page + 1, data_id=data_id)

    def beautiful_soup(self, link):
        social_links = []
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.122 Safari/537.36 '
        }
        res = requests.request("GET", link, headers=headers)
        profileLink_soup = BeautifulSoup(res.content, 'lxml')
        zsg_button = profileLink_soup.find('a', {'class': 'show-lightbox zsg-button'})
        socials = profileLink_soup.find('dd', {'class': 'profile-information-websites'})
        broker_address = profileLink_soup.find('dd', {'class': 'profile-information-address'})
        screen_name = profileLink_soup.find('dd', {'class': 'profile-information-screen-name'})
        member_since = profileLink_soup.find('dd', {'class': 'profile-information-memeber-since'})
        # real_estate_license = profileLink_soup.find('div', {'class': 'real-estate-license-area'})
        # other_license = profileLink_soup.find(class_='yui3-toggle-content-minimized license-area')
        if broker_address:
            social_links.append(broker_address.getText().strip())
        else:
            social_links.append('')
        if screen_name:
            social_links.append(screen_name.getText().strip())
        else:
            social_links.append('')
        if member_since:
            social_links.append(member_since.getText().strip())
        else:
            social_links.append('')
        # if real_estate_license:
        #     social_links.append(real_estate_license.getText().strip())
        # else:
        #     social_links.append('')
        # if other_license:
        #     social_links.append(other_license.getText().strip())
        # else:
        #     social_links.append('')
        if socials:
            socials_dom = socials.find_all('a')
            for social_dom in socials_dom:
                social_links.append(social_dom['href'])
        if zsg_button and zsg_button.has_attr('data-zuid'):
            data_id = profileLink_soup.find('a', {'class': 'show-lightbox zsg-button'})['data-zuid']
            return self.get_sale(page=1, data_id=data_id), social_links
        else:
            return [[]], social_links

    def get_location(self, page, count=1):
        if re.match(r'^-?\d+(?:\.\d+)?$', self.location[0]) is None:
            self.location = ' '.join(self.location)
            url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=%s' \
                  '&locationText=%s' % (
                      page, self.location)
        else:
            url = 'https://www.zillow.com/ajax/directory/DirectoryContent.htm?apiVer=1&jsonVer=1&sortBy=None&page=%s' \
                  '&locationText=%s' % (
                      page, self.location[0])
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.122 Safari/537.36 '
        }
        response = requests.request("GET", url, headers=headers)
        try:
            parse = json.loads(response.text)['model']['viewModel']['boards']
        except ValueError as v:
            print(v)
            count += 1
            if count > 2:
                return self.lines
            self.get_location(page=page+1, count=count+1)
        if not parse['boards']:
            return self.lines
        for board in parse['boards']:
            profileLink = 'https://www.zillow.com' + board['href']
            sales, links = self.beautiful_soup(profileLink)
            if sales:
                print(profileLink)
            line = json_parse(board=board)
            for sale in sales:
                print(sale)
                if len(sale) < 4:
                    continue
                tmp_line = [sale[0], sale[1], sale[2], sale[3], line[0], line[2]]
                for link in links:
                    tmp_line.append(link)
                print(tmp_line)
                self.write_csv(w_lines=[tmp_line], filename='Zillow.csv')
                self.lines.append(tmp_line)
                self.write_excel(e_lines=self.lines)
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/80.0.3987.122 Safari/537.36 '
            }
            res = requests.request("GET", profileLink, headers=headers)
            profileLink_soup = BeautifulSoup(res.content, 'lxml')
            members = profileLink_soup.find_all('a', {'class': re.compile('ptm-member-image-container')})
            if members:
                if profileLink_soup.find(class_='ctcd-user-name'):
                    member_name = profileLink_soup.find(class_='ctcd-user-name').getText()
                else:
                    member_name = ''
                if profileLink_soup.find('dt', text=re.compile('phone:')):
                    member_phone = profileLink_soup.find('dt', text=re.compile('phone:')).find_next('dd').getText()
                else:
                    member_phone = ''
                for member in members:
                    member_link = 'https://zillow.com' + member['href']
                    member_sales, member_links = self.beautiful_soup(member_link)
                    if member_sales:
                        print(member_link)
                    for member_sale in member_sales:
                        if len(member_sale) < 4:
                            continue
                        member_line = [member_sale[0], member_sale[1], member_sale[2], member_sale[3], member_name,
                                       member_phone]
                        for m in member_links:
                            member_line.append(m)
                        # social_site = profileLink_soup.find('dd', {'class': 'profile-information-websites'})
                        # if social_site:
                        #     for social_link in social_site.find_all('a'):
                        #         member_line.append(social_link['href'])
                        # if not member_line in self.lines:
                        #     self.lines.append(member_line)
                        print(member_line)
                        self.write_csv(w_lines=[member_line], filename='Zillow.csv')
                        self.write_excel(e_lines=lines)
        return self.get_location(page=page+1)


if __name__ == '__main__':
    print('===============================Start=================================')
    z = Z()
    records = z.get_location(page=1, count=1)
    records.sort(key=lambda x: (datetime.strptime(x[2], '%m/%d/%Y'), x[0], x[1], x[3], x[4]), reverse=True)
    z.write_csv(w_lines=records, filename='Zillow_Sort.csv')
    print('================================The End=================================')
