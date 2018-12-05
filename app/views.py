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
	
	url = request.form['url']
	HEADER = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}
	DOWNLOAD_FOLDER = "/home/choiys/am2pm/app/download/"

	dlist = os.listdir(DOWNLOAD_FOLDER)
	if len(dlist) != 0:
		dlist.sort()
		dstatus = dlist[-1]
		dpath = DOWNLOAD_FOLDER+str(int(dstatus)+1)+'/'
		os.mkdir(dpath)
	else:
		dpath = DOWNLOAD_FOLDER+'1/'
		os.mkdir(dpath)

	def complete_url(url, base_url):
		if ("http://" in url) or ("https://" in url):
			return url

		else:
			return base_url+"/"+url

	def download(s, url, file_name):
		if file_name != "":
			with open(dpath+file_name, "wb") as f:
				res = s.get(url)
				f.write(res.content)

	def filter(file_name):
		file_type = m.from_file(dpath+file_name)
		if "HTML" in file_type:
			os.remove(dpath+file_name)

	def split_link(type, link, base_url):
		if type == 1:
			link = complete_url(link, base_url)
			file_name = link.split("/")[-1]
		else:
			link = complete_url(str(link).split("href=\"")[1].split("\"")[0], base_url)
			file_name = link.split("/")[-1]
		
		return link, file_name

	m = magic.Magic()

	s = requests.Session()
	r = s.get(url, headers=HEADER)
	soup = BeautifulSoup(r.text, 'html.parser')

	all_atags = soup.find_all('a')
	delete_queue = []

	data = split_link(2, all_atags, url)
	for atag in all_atags:
		link, file_name = split_link(2, atag, url)
		download(s, link, file_name)

	files = os.listdir(dpath)

	for f in files:
		filter(f)

	flash('Download is successfully done!')
	return render_template('index.html', done=True)
