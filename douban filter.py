import re
import io
import sys
import urllib.request
from xml.etree import ElementTree

class Topic(object):
	def __init__(self, url, title, reply, group):
		self.url = url
		self.title = title
		self.reply = reply
		self.group = group

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

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码

cur_page_no = 1

print("loading...")
group_url = 'https://www.douban.com/group/'
req = urllib.request.Request(group_url)
req.add_header('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36")
req.add_header('Host', "www.douban.com")
req.add_header('Scheme', "https")
req.add_header('Version', "HTTP/1.1")
req.add_header('Referer', group_url)
req.add_header('Cookie', 'bid="tPUrC0sGWyU"; ll="108288"; _ga=GA1.2.273173056.1453032179; ps=y; ue="Vigi0303@163.com"; dbcl2="60652504:BGlb29Fu1J4"; ct=y; ck=s53H; ap=1; push_noty_num=0; push_doumail_num=0; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1462631780%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_id.100001.8cb4=ccab1e82873542ba.1453124943.36.1462631780.1462615040.; _pk_ses.100001.8cb4=*; __utmt=1; __utma=30149280.273173056.1453032179.1462614717.1462631781.90; __utmb=30149280.2.10.1462631781; __utmc=30149280; __utmz=30149280.1462614717.89.50.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmv=30149280.6065')
url_content = urllib.request.urlopen(req).read().decode("utf-8", "ignore")

url_filter = BlackFilter("black_list.txt")
title_filter = BlackFilter("black_title_list.txt")

url_list = []
topic_list = []
is_quit = False

m = url_content.index("<table class=\"olt\">")
n = url_content.index("</table>", m)
table_content = url_content[m:n+8]
table = ElementTree.XML(table_content)
for tr in table[0]:
	topic_url = tr[0][0].attrib["href"]
	title = tr[0][0].attrib["title"]
	reply = tr[1].text
	group = tr[3][0].text
	topic = Topic(topic_url, title, reply, group)
	if url_filter.contain(topic_url):
		continue
	if title_filter.contain(title):
		continue
	print("============================")
	print(topic.title)
	print(topic.url)
	print(topic.reply)
	print(topic.group)
	print("============================")
	print("pass it and add check it later: y")
	print("pass it and add to black list: n")
	print("quit program and save: q")
	choose = input("enter your choose: ")
	if choose == "y":
		if topic_url not in url_list:
			url_list.append(topic_url)
			topic_list.append(topic)
		print("saved-->",topic_url)
	elif choose == "n":
		url_filter.append(topic_url)
		title_filter.append(title)
		print("ignore-->",topic_url)
	elif choose == "q":
		is_quit = True
		break
	else:
		print("wrong input and next")
	print("")

url_filter.save()
title_filter.save()

print("end program")