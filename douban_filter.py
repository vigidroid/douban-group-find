# encoding: utf-8

import re
import io
import sys
import time
import urllib.request
import logging
from xml.etree import ElementTree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码

COOKIE_STR = ""
try:
	with open("把cookie拷贝到这个文件里.txt", "r", encoding="utf-8") as f:
		COOKIE_STR = f.read()
except Exception as e:
	print("读取文件错误 -->","把cookie拷贝到这个文件里.txt")
	exit()

class Topic(object):
	def __init__(self, url, title, reply, time, group):
		self.url = url
		self.title = title
		self.reply = reply
		self.update_time = time
		self.group = group
		self.user_name = None
		self.user_url = None
		self.submit_time = None
		self.topic_content = None

class NetWordUtil(object):
	net_work_time = 0
	def request(url):
		NetWordUtil.net_work_time += 1
		if NetWordUtil.net_work_time > 4:
			time.sleep(2)
			NetWordUtil.net_work_time = 0
		proxy = "http://127.0.0.1:1080"
		proxy_support = urllib.request.ProxyHandler({'http': proxy})
		opener = urllib.request.build_opener(proxy_support)
		urllib.request.install_opener(opener)
		req = urllib.request.Request(url)
		req.add_header('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36")
		req.add_header('Host', "www.douban.com")
		req.add_header('Scheme', "https")
		req.add_header('Version', "HTTP/1.1")
		req.add_header('Referer', url)
		req.add_header('Cookie', COOKIE_STR)
		url_content = urllib.request.urlopen(req).read().decode("utf-8", "ignore")
		return url_content

class BlackFilter(object):
	def __init__(self, file_name):
		self.file_name = file_name
		self.black_list = []
		with open(self.file_name, "r", encoding="utf-8") as f:
			for line in f.readlines():
				line = line.strip()
				if not len(line):
					continue
				self.black_list.append(line)
	def contain(self, item):
		return item in self.black_list
	def append(self, item):
		if item not in self.black_list:
			self.black_list.append(item)
	def save(self):
		first_line = True
		with open(self.file_name, "w", encoding="utf-8") as f:
			for item in self.black_list:
				if first_line:
					first_line = False
				else:
					f.write("\n")
				f.write(item)

class KeyWordFilter(BlackFilter):
	def contain(self, item):
		for black in self.black_list:
			if black in item:
				return True
		return False

class TopicProvider(object):
	def __init__(self):
		self.url_filter = BlackFilter("black_url_list.txt")
		self.title_key_word_filter = KeyWordFilter("title_key_word.txt")
		self.user_filter = BlackFilter("black_user_list.txt")
		self.content_key_word_filter = KeyWordFilter("content_black_word.txt")
		self.queue = []   # 缓存一页的topic
		self.passedQueue = []    # 缓存已经被排除过的topic，可以避免多余的fetch detail操作
		pass
	def findInCloud(self, page_no):
		print("loading... at page " + str(page_no))
		sys.stdout.flush()
		topic_list = []
		group_url = 'https://www.douban.com/group/'
		if page_no > 1:
			group_url = group_url + "?start=" + str(50 * (page_no - 1))
		url_content = NetWordUtil.request(group_url)
		m = url_content.index('<table class="olt">')
		n = url_content.index("</table>", m)
		table_content = url_content[m:n+8]
		table = ElementTree.XML(table_content)
		for tr in table[0]:
			topic_url = tr[0][0].attrib["href"]
			title = tr[0][0].attrib["title"]
			reply = int(tr[1].text[0:tr[1].text.index("回应")])
			time = tr[2].attrib["title"]
			group = tr[3][0].text
			topic_list.append(Topic(topic_url, title, reply, time, group))
		return topic_list
	def fetchDetail(self, topic):
		url_content = NetWordUtil.request(topic.url)
		user_m = url_content.index('<span class="from">')
		user_n = url_content.index("</span>", user_m)
		user_content = url_content[user_m:user_n+7]
		user_span = ElementTree.XML(user_content)
		topic.user_name = user_span[0].text
		topic.user_url = user_span[0].attrib['href']
		time_m = url_content.index('<span class="create-time', user_n)
		time_n = url_content.index('</span>', time_m)
		time_content = url_content[time_m:time_n+7]
		time_span = ElementTree.XML(time_content)
		topic.submit_time = time_span.text
		content_m = url_content.index('<div class="topic-content">')
		content_n = url_content.index('<div class="topic-opt clearfix">')
		topic.topic_content = url_content[content_m:content_n]
		return topic
	def filter(self, topic):
		white_word_list = [ '望京', '花家地', '太阳宫', '安贞', '芍药居'
							'惠新西街', '北土城', '央美', '酒仙桥', '阜通'
							'10号线', '十号线', '和平西桥', '大西洋']
		is_match = False     # True to disable white word list

		if topic.url in url_list:
			return False
		if topic.reply > 10:
#			print("topic.reply =",topic.reply,"in",topic.title)
			return False
		if self.title_key_word_filter.contain(topic.title):
#			print("found key word in",topic.title)
			return False
		if self.content_key_word_filter.contain(topic.title):
			return False
		if self.url_filter.contain(topic.url):
#			print("found black url",topic.url)
			return False
		try:
			topic = self.fetchDetail(topic)
		except Exception as e:
			print("strange topic",topic.url)
			return True
		if self.user_filter.contain(topic.user_url):
#			print("found black user",topic.user_name,"in",topic.url)
			return False
		if self.content_key_word_filter.contain(topic.topic_content):
#			print("found key word in",topic.url)
			return False
		for white in white_word_list:
			if white in topic.title:
				is_match = True
				break
			if white in topic.topic_content:
				is_match = True
				break
		if not is_match:
			return False
		return True
	def provide(self):
		cur_page_no = 0
		while cur_page_no < 500:
			# find in cache queue
			while len(self.queue):
				topic = self.queue.pop(0)
				if topic.url in self.passedQueue:
					print("pass ",topic.url)
				elif self.filter(topic):
					return topic
				else:
					self.passedQueue.append(topic.url)
					print("skip ",topic.url)
			# find in cloud
			cur_page_no += 1
			temp_list = self.findInCloud(cur_page_no)
			if not len(temp_list):
				return None
			self.queue.extend(temp_list)
		return None

url_list = []
provider = TopicProvider()
is_quit = False
while not is_quit:
	try:
		topic = provider.provide()
	except Exception as e:
		logging.exception(e)
		break
	if topic is None:
		is_quit = True
		print("no data .....")
		break
	print("============================")
	print(topic.title)
	print(topic.url)
	print("用户名：",topic.user_name)
	print("提交时间：",topic.submit_time," ",topic.reply,"回应")
	print("更新时间：",topic.update_time)
	print(topic.group)
	print("============================")
	print("skip it(only skip in this session): s")
	print("never see this thread again: n")
	print("block all topic by this user: u")
	print("quit program and save: q")
	choose = input("enter your choose: ")
	if choose == "s":
		if topic.url not in url_list:
			url_list.append(topic.url)
	elif choose == "n":
		provider.url_filter.append(topic.url)
	elif choose == "u":
		provider.user_filter.append(topic.user_url)
	elif choose == "q":
		is_quit = True
	else:
		print("wrong input and next")
	print("")

provider.url_filter.save()
provider.user_filter.save()

print("end program")