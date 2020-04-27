from scrapy import Spider, Request
from tedtalks.items import TedtalksItem

import requests

class TedSpider(Spider):
	name = 'tedtalks_spider'
	allowed_urls = ['https://www.ted.com/']
	start_urls = ['https://www.ted.com/talks?page=1']
	
	def parse(self,response):
		num_pages =  int(response.xpath('//a[@class="pagination__item pagination__link"]//text()').extract()[-1])
		page_urls = [f'https://www.ted.com/talks?page={i+1}' for i in range(num_pages)] 

		for url in page_urls:
			yield Request(url=url,callback=self.parse_result_page)

	def parse_result_page(self,response):
		talk_urls = response.xpath('//div[@class="media__message"]//@href').extract()
		talk_urls = [f'https://www.ted.com{url}' for url in talk_urls]
	
		for url in talk_urls:
			yield Request(url = url, callback = self.parse_talk_page)

	def parse_talk_page(self, response):
		talk_title = response.xpath('//meta[@property="og:title"]/@content').extract()
		talk_speaker = response.xpath('//meta[@name="author"]/@content').extract()[0]
		talk_view_num = response.xpath('//span/text()').extract()[response.xpath('//span/text()').extract().index(' views')-1].strip()
		talk_view_num = ''.join(talk_view_num.split(','))
		talk_categories = response.xpath('//meta[@property="og:video:tag"]/@content').extract()
		
		talk_length = response.xpath('//span/text()').extract()[response.xpath('//span/text()').extract().index(' views')+2][3:].strip()

		meta = {'talk_title': talk_title, 'talk_speaker':talk_speaker,'talk_view_num': talk_view_num,'talk_categories':talk_categories, 'talk_length':talk_length}

		new_url = ''.join([response.url,'/transcript'])	
	
		req = requests.get(new_url)
		
		if req.status_code == 404:
			item = TedtalksItem()
			item['title'] = talk_title
			item['speaker'] = talk_speaker
			item['view_num'] = talk_view_num
			item['categories'] = talk_categories
			item['length'] = talk_length
			item['transcrpit'] = ''
			yield item

		else:
			yield Request(url=new_url, callback=self.parse_transcript_page, meta=meta)


	def parse_transcript_page(self,response):
		talk_title = response.meta['talk_title'][0]
		talk_speaker = response.meta['talk_speaker']
		talk_view_num = response.meta['talk_view_num']
		talk_categories = response.meta['talk_categories']
		talk_length = response.meta['talk_length']

		talk_transcrpit = response.xpath('//p//text()').extract()
		temp = list(map(lambda s: s.replace('\"','').replace('\'','').split('\n'),talk_transcrpit))  
		temp = sum(list(map(lambda s: s.split('\t'),sum(temp,[]))),[])
		talk_transcrpit = ''.join(list(filter(None, temp))) 

		item = TedtalksItem()
		item['title'] = talk_title
		item['speaker'] = talk_speaker
		item['view_num'] = talk_view_num
		item['categories'] = talk_categories
		item['length'] = talk_length
		item['transcrpit'] = talk_transcrpit

		yield item