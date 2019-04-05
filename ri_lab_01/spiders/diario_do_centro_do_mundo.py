# -*- coding: utf-8 -*-
import scrapy
import json

from dateutil import parser
import datetime

from ri_lab_01.items import RiLab01Item
from ri_lab_01.items import RiLab01CommentItem


class DiarioDoCentroDoMundoSpider(scrapy.Spider):
    name = 'diario_do_centro_do_mundo'
    allowed_domains = ['diariodocentrodomundo.com.br']
    start_urls = []
    official_link = 'https://www.diariodocentrodomundo.com.br/'
    limitDate = datetime.datetime(2018, 1, 1)
    limitCount = 350

    def __init__(self, *a, **kw):
        super(DiarioDoCentroDoMundoSpider, self).__init__(*a, **kw)
        with open('seeds/diario_do_centro_do_mundo.json') as json_file:
                data = json.load(json_file)
        self.start_urls = list(data.values())

    def parse(self, response):

        section = self._extractSectionFromUrl(response.url)
        initialLink = response.css('.td_block_wrap a::attr(href)').get()

        limitLinksToFollow = 50 if (self.limitCount - 50) >= 0 else (self.limitCount % 50)

        if(self._isValidLink(initialLink) and self._isNotVideo(initialLink) and limitLinksToFollow > 0):
            yield response.follow(initialLink, self.parse_content , meta={ 'section': section, 'counterLimit': limitLinksToFollow })

        self.limitCount -= 50


    def parse_content(self, response):

        section = response.meta['section']
        limitLinks = response.meta['counterLimit']
        subtract = 0

        def _extractFromCSS(selector):
            return response.css(selector)

        parsedDate = self._formatDate(_extractFromCSS('.entry-date ::attr(datetime)').get())

        contentDraft = {
            'title': _extractFromCSS('h1.entry-title::text').get(),
            'subtitle': '',
            'author': _extractFromCSS('.td-post-author-name a::text').get(),
            'date': parsedDate,
            'section': section,
            'text': ' '.join(_extractFromCSS('.td-post-content > p ::text').getall()),
            'url': response.url
        }

        if (contentDraft['text'].strip() != '' and parser.parse(parsedDate) > self.limitDate):
            subtract = 1

            yield {
                'título': contentDraft['title'],
                'subtítulo': '',
                'autor': contentDraft['author'],
                'data': contentDraft['date'],
                'seção': contentDraft['section'],
                'texto': contentDraft['text'],
                'url': contentDraft['url']
            }

        nextLink = _extractFromCSS('.td-post-next-prev-content > a::attr(href)').get()

        if(limitLinks > 0):
            yield response.follow(nextLink, self.parse_content, meta={ 'section': section, 'counterLimit': limitLinks - subtract })

    def _formatDate(self, date):
        datetime_object = parser.parse(date)
        datetime_object_brazil = datetime_object - datetime.timedelta(hours=3)
        return datetime_object_brazil.strftime('%d/%m/%Y %H:%M:%S')

    def _isNotVideo(self, link):
        return link[len(self.official_link):].split('-')[0] != 'video'

    def _extractSectionFromUrl(self, url):
        return url[41:][:-1]

    def _isValidLink(self, link):
        return link[:41] == self.official_link