import re
import io
import sys
import time
import urllib.request
from xml.etree import ElementTree

class Topic(object):
	def __init__(self, url, title, reply, group):
		self.url = url
		self.title = title
		self.reply = reply
		self.group = group
		self.user_name = None
		self.user_url = None
		self.submit_time = None
		self.topic_content = None

class NetWordUtil(object):
	net_work_time = 0
	def request(url):
		NetWordUtil.net_work_time += 1
		if NetWordUtil.net_work_time > 5:
			time.sleep(2)
			NetWordUtil.net_work_time = 0
		req = urllib.request.Request(url)
		req.add_header('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36")
		req.add_header('Host', "www.douban.com")
		req.add_header('Scheme', "https")
		req.add_header('Version', "HTTP/1.1")
		req.add_header('Referer', url)
		req.add_header('Cookie', 'bid="tPUrC0sGWyU"; ll="108288"; _ga=GA1.2.273173056.1453032179; ps=y; ue="Vigi0303@163.com"; dbcl2="60652504:BGlb29Fu1J4"; ct=y; ck=s53H; ap=1; push_noty_num=0; push_doumail_num=0; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1462631780%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_id.100001.8cb4=ccab1e82873542ba.1453124943.36.1462631780.1462615040.; _pk_ses.100001.8cb4=*; __utmt=1; __utma=30149280.273173056.1453032179.1462614717.1462631781.90; __utmb=30149280.2.10.1462631781; __utmc=30149280; __utmz=30149280.1462614717.89.50.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmv=30149280.6065')
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
		self.content_key_word_filter = KeyWordFilter("content_key_word.txt")
		self.queue = []
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
			group = tr[3][0].text
			topic_list.append(Topic(topic_url, title, reply, group))
		return topic_list
	def fetchDetail(self, topic):
		url_content = NetWordUtil.request(topic.url)
		user_m = url_content.index('<span class="from">')
		user_n = url_content.index("</span>", user_m)
		user_content = url_content[user_m:user_n+7]
		user_span = ElementTree.XML(user_content)
		topic.user_name = user_span[0].text
		topic.user_url = user_span[0].attrib['href']
		time_m = url_content.index('<span class="color-green">', user_n)
		time_n = url_content.index('</span>', time_m)
		time_content = url_content[time_m:time_n+7]
		time_span = ElementTree.XML(time_content)
		topic.submit_time = time_span.text
		content_m = url_content.index('<div class="topic-content">')
		content_n = url_content.index('<div class="topic-opt clearfix">')
		topic.topic_content = url_content[content_m:content_n]
		return topic
	def filter(self, topic):
		if topic.reply > 30:
#			print("topic.reply =",topic.reply,"in",topic.title)
			return False
		if '望京' not in topic.title:
			return False
		if self.title_key_word_filter.contain(topic.title):
#			print("found key word in",topic.title)
			return False
		if self.url_filter.contain(topic.url):
#			print("found black url",topic.url)
			return False
		topic = self.fetchDetail(topic)
		if self.user_filter.contain(topic.user_url):
#			print("found black user",topic.user_name,"in",topic.url)
			return False
		if self.content_key_word_filter.contain(topic.topic_content):
#			print("found key word in",topic.url)
			return False
		return True
	def provide(self):
		cur_page_no = 0
		while cur_page_no < 500:
			# find in cache queue
			while len(self.queue):
				topic = self.queue.pop(0)
				if self.filter(topic):
					return topic
			# find in cloud
			cur_page_no += 1
			temp_list = self.findInCloud(cur_page_no)
			if not len(temp_list):
				return None
			self.queue.extend(temp_list)
		return None

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码

url_list = []
provider = TopicProvider()
is_quit = False
while not is_quit:
	topic = provider.provide()
	if topic is None:
		is_quit = True
		print("no data .....")
	print("============================")
	print(topic.title)
	print(topic.url)
	print("用户名：",topic.user_name)
	print("提交时间：",topic.submit_time," ",topic.reply,"回应")
	print(topic.group)
	print("============================")
	print("pass it and check it later: y")
	print("pass it and add to black list: n")
	print("quit program and save: q")
	choose = input("enter your choose: ")
	if choose == "y":
		if topic.url not in url_list:
			url_list.append(topic.url)
	elif choose == "n":
		provider.url_filter.append(topic.url)
	elif choose == "q":
		is_quit = True
	else:
		print("wrong input and next")
	print("")

provider.url_filter.save()

print("end program")