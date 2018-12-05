from flask import request
from flask import Response
from flask import render_template
from flask import redirect
from flask import session
from flask import flash
from app import app
from bs4 import BeautifulSoup
from multiprocessing import Pool
import os
import requests
import re
import magic
import time


@app.route('/')
def main():
	return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route('/test')
def test_origin():
	report_list = os.listdir('/home/choiys/cuckoo/.cuckoo/storage/analyses/')
	report_temp = os.listdir('/home/choiys/am2pm/app/templates/reports/')
	print(len(report_list))
	report_list.sort()
	report_list = report_list[0:-1]
	report_list.sort(key=int)
	try:
		num = report_list[-1]
	except:
		num = 0
	if int(num) > len(report_temp)-1:
		for i in range(len(report_temp), int(num)+1):
			src = '/home/choiys/cuckoo/.cuckoo/storage/analyses/'+str(i)+'/reports/report.html'
			dst = '/home/choiys/am2pm/app/templates/reports/'+str(i)+'.html'
			try:
				os.symlink(src, dst)
			except:
				print("symlink Failed!", str(i))
	return render_template('test.html', num = int(num))
	

@app.route('/test/<passed_num>')
def test(passed_num):
	report_list = os.listdir('/home/choiys/cuckoo/.cuckoo/storage/analyses/')
	report_temp = os.listdir('/home/choiys/am2pm/app/templates/reports/')
	report_list.sort()
	report_list = report_list[1:-1]
	report_list.sort(key=int)
	num = report_list[-1]
	if int(num) > len(report_temp)-1:
		for i in range(len(report_temp), int(num)+1):
			src = '/home/choiys/cuckoo/.cuckoo/storage/analyses/'+str(i)+'/reports/report.html'
			dst = '/home/choiys/am2pm/app/templates/reports/'+str(i)+'.html'
			try:
				os.symlink(src, dst)
			except:
				print("symlink Failed!", str(i))
	
	if passed_num:
		return render_template('test.html', num = int(num), passed_num = int(passed_num))
	else:
		return render_template('test.html', num = int(num))

@app.route('/report/<num>')
def report(num):
	return render_template('reports/'+num+'.html')

@app.route('/search', methods=['POST'])
def search():
	temp = 0
	url = request.form['url']
	if "http://" not in url and "https://" not in url:
		url = "http://" + url
	base_url = url.split('/')[0]+'//'+url.split('/')[2]+'/'
	HEADER = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}
	DOWNLOAD_FOLDER = "/home/choiys/am2pm/app/download/"

	dlist = os.listdir(DOWNLOAD_FOLDER)
	dnum = '1'
	if len(dlist) != 0:
		dlist.sort(key=int)
		dstatus = dlist[-1]
		dnum = str(int(dstatus)+1)
		dpath = DOWNLOAD_FOLDER+dnum+'/'
		os.mkdir(dpath)
	else:
		dpath = DOWNLOAD_FOLDER+'1/'
		os.mkdir(dpath)

	def complete_url(url, base_url):
		if ("http://" in url) or ("https://" in url):
			return url

		else:
			return base_url+"/"+url

	def download(s, url, file_name, temp):
		if file_name != "" and "javascript:" not in file_name and "javascript:" not in url:
			if len(file_name)>50:
				file_name = file_name[:50]
			if len(file_name.split('.')[-1]):
				file_name = str(temp)
				temp += 1
			with open(dpath+file_name, "wb") as f:
				try:
					res = s.get(url, headers=HEADER, verify=False)
					f.write(res.content)
				except:
					pass
		return temp

	def filter(file_name):
		file_type = m.from_file(dpath+file_name)
		if "HTML" in file_type or "empty" in file_type:
			os.remove(dpath+file_name)
		elif "Hangul" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".hwp")
		elif "PDF" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".pdf")
		elif "PowerPoint" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".pptx")
		elif "Excel" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".xlsx")
		elif "Word" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".docx")
		elif "Zip" in file_type or "zip" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".zip")
		elif "PE32" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".exe")
		elif "ASCII" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".txt")

	def split_link(type, link, base_url):
		if type == 1:
			link = complete_url(link, base_url)
			file_name = link.split("/")[-1]
		else:
			try:
				link = complete_url(str(link).split("href=\"")[1].split("\"")[0], base_url)
			except:
				link = "http://choiys.tistory.com"
			file_name = link.split("/")[-1]
		if "javascript:" in link:
			link = "http://choiys.tistory.com"
			file_name = ""
		else:
			link = link.replace("&amp;", "&").replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
			file_name = file_name.replace("&amp;", "&").replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
		return link, file_name

	m = magic.Magic()

	s = requests.Session()
	r = s.get(url, headers=HEADER, verify=False)
	soup = BeautifulSoup(r.text, 'html.parser')

	all_atags = soup.find_all('a')
	delete_queue = []

	for atag in all_atags:
		link, file_name = split_link(2, atag, base_url)
#		print link
		temp = download(s, link, file_name, temp)

	files = os.listdir(dpath)
	time.sleep(1)
	for f in files:
		filter(f)

	files = os.listdir(dpath)
	count = len(files)
	return render_template('index.html', download=True, count=count, num=dnum)

@app.route('/submit', methods=['POST'])
def submit():
	DOWNLOAD_FOLDER = "/home/choiys/am2pm/app/download/"
	num = request.form['num']
	dpath = DOWNLOAD_FOLDER+str(num)+'/'
	dlist = os.listdir(dpath)
	if len(dlist) != 0:
		msg = ". /home/choiys/cuckoo/bin/activate;"
		for f in dlist:
			msg += "cuckoo --cwd ~/cuckoo/.cuckoo submit --timeout 60 "
			msg += dpath+str(f)+"&&"
		msg = msg[:-2]
	
		os.system(msg)

		time.sleep(60)

	return render_template('index.html', submit=True)
