from flask import request
from flask import Response
from flask import render_template
from flask import redirect
from flask import session
from flask import flash
from app import app
from bs4 import BeautifulSoup
from multiprocessing import Pool
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import requests
import re
import magic
import time
import json
import sys
import pickle

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

@app.route('/')
def main():
	stat_path = "/home/choiys/am2pm/app/statistics"
	stat = []
	with open(stat_path, "rb") as f:
		try:
			stat = pickle.load(f)
		except:
			pass
	return render_template('index.html', stat = stat)

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route('/test/')
def test_origin():
	dpath = "/home/choiys/cuckoo/.cuckoo/storage/analyses/"
	dnum = len(os.listdir(dpath))-1
	if dnum < 0:
		dnum = 0

	return redirect('/test/'+str(dnum))

@app.route('/test/<passed_num>')
def test(passed_num):
	stat_path = "/home/choiys/am2pm/app/statistics"
	stat = []
	with open(stat_path, "rb") as f:
		try:
			stat = pickle.load(f)
		except:
			pass
	report_list = os.listdir('/home/choiys/cuckoo/.cuckoo/storage/analyses/')
	report_temp = os.listdir('/home/choiys/am2pm/app/templates/reports/')
	report_list.sort()
	report_list = report_list[0:-1]
	report_list.sort(key=int)
	with open("/home/choiys/am2pm/app/current", "r") as f:
		end_num = int(f.readline())
		count_num = int(f.readline())
		links = json.loads(f.readline())
	with open("/home/choiys/am2pm/app/av", "r") as f:
		data = json.loads(f.readline())
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

	dpath = "/home/choiys/cuckoo/.cuckoo/storage/analyses/"
	dnum = len(os.listdir(dpath))-1
	risk_cnt = 0
	for i in range(dnum-count_num+1, dnum+1):
		with open("/home/choiys/cuckoo/.cuckoo/storage/analyses/"+str(i)+"/reports/report.html", "r") as f:
			lines = f.read()
			ok = re.findall("<strong>name: </strong> (.*?)</li>", lines[400000:450000])
			if ok:
				fname = ok[0]
				with open("/home/choiys/cuckoo/.cuckoo/storage/analyses/"+str(i)+"/reports/report.json", "r") as f2:
					jsonline = f2.read(1024)
					ok2 = re.findall("\"score\": (.*?),", jsonline)
					if ok2:
						score = ok2[0]
						data[fname]['score'] = float(score)
			data[fname]['num'] = i
		
			   
		if (data[fname]['score'] >= 4 and (float(data[fname]['count'])/data[fname]['total'])*100 >= 40) or (data[fname]['score'] >= 10) or ((float(data[fname]['count'])/data[fname]['total'])*100 >= 60):
			risk_cnt += 1
			risk = 3
		elif (data[fname]['score'] >= 2 and (float(data[fname]['count'])/data[fname]['total'])*100 >= 20) or (data[fname]['score'] >= 5) or ((float(data[fname]['count'])/data[fname]['total'])*100 >= 40):
			risk_cnt += 1
			risk = 2
		elif (data[fname]['score'] >= 1 or (float(data[fname]['count'])/data[fname]['total'])*100 >= 10):
			risk = 1
		else:
			risk = 0

		data[fname]['risk'] = risk

	stat_temp = {'url': data['url'].split('/')[2], 'risk': risk_cnt}
	if len(stat) == 6:
		del stat[0]

	flag = True
	for i in range(len(stat)):
		if stat[i]['url'] == data['url'].split('/')[2]:
			flag = False
	if flag:
		stat.append(stat_temp)
		
	with open(stat_path, "wb") as f:
		pickle.dump(stat, f)
	
	return render_template('test.html', num = int(num), end_num = end_num, count_num = count_num, links = links, data = data, passed_num = int(passed_num))

@app.route('/report/<num>/')
def report(num):
	if str(num) == 'latest':
		return render_template('reports/latest.html')
	return render_template('reports/'+num+'.html')


@app.route('/search', methods=['POST'])
def search():
	stat_path = "/home/choiys/am2pm/app/statistics"
	stat = []
	with open(stat_path, "rb") as f:
		try:
			stat = pickle.load(f)
		except:
			pass

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
##############################20:53 delete '/'############################
			return base_url+url

	def download(s, url, file_name, temp, links):
		ht = url.split('/')[0]+'//'
		ur = url.split(ht)[1]
		while(len(ur.split('//'))>1):
			ur = ur.replace('//', '/')
		url = ht+ur
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
					links[file_name] = url
				except:
					pass

		return temp, links

	def filter(file_name, links):
		file_type = m.from_file(dpath+file_name)
		if "HTML" in file_type or "empty" in file_type:
			os.remove(dpath+file_name)
			del links[file_name]
		elif "Hangul" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".hwp")
			links[file_name+'.hwp'] = links[file_name]
			del links[file_name]
		elif "PDF" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".pdf")
			links[file_name+'.pdf'] = links[file_name]
			del links[file_name]
		elif "PowerPoint" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".pptx")
			links[file_name+'.pptx'] = links[file_name]
			del links[file_name]
		elif "Excel" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".xlsx")
			links[file_name+'.xlsx'] = links[file_name]
			del links[file_name]
			links[file_name] = dpath+file_name+".xlsx"
		elif "Word" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".docx")
			links[file_name+'.docx'] = links[file_name]
			del links[file_name]
		elif "Zip" in file_type or "zip" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".zip")
			links[file_name+'.zip'] = links[file_name]
			del links[file_name]
		elif "PE32" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".exe")
			links[file_name+'.exe'] = links[file_name]
			del links[file_name]
		elif "ASCII" in file_type:
			os.rename(dpath+file_name, dpath+file_name+".txt")
			links[file_name+'.txt'] = links[file_name]
			del links[file_name]
	
		return links

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
	links = {'url': url}
	for atag in all_atags:
		link, file_name = split_link(2, atag, base_url)
#		print link
		temp, links = download(s, link, file_name, temp, links)

	files = os.listdir(dpath)
	time.sleep(1)
	for f in files:
		links = filter(f, links)

	with open("/home/choiys/am2pm/app/linkdata", "w") as fd:
		links = json.dumps(links)
		fd.write(links)

	files = os.listdir(dpath)
	count = len(files)
	
	return render_template('index.html', download=True, count=count, num=dnum, stat = stat)

@app.route('/submit', methods=['POST'])
def submit():
	stat_path = "/home/choiys/am2pm/app/statistics"
	stat = []
	with open(stat_path, "rb") as f:
		try:
			stat = pickle.load(f)
		except:
			pass

	DOWNLOAD_FOLDER = "/home/choiys/am2pm/app/download/"
	num = request.form['num']
	with open("/home/choiys/am2pm/app/linkdata", "r") as fd:
		links = fd.readline()
		links = json.loads(links)
	dpath = DOWNLOAD_FOLDER+str(num)+'/'
	dlist = os.listdir(dpath)
	if len(dlist) != 0:
		msg = ". /home/choiys/cuckoo/bin/activate;"
		for f in dlist:
			msg += "cuckoo --cwd ~/cuckoo/.cuckoo submit --timeout 20 "
			msg += dpath+str(f)+"&&"
		msg = msg[:-2]
	
		os.system(msg)
		time.sleep(float(30*len(dlist)))
	
	num_path = "/home/choiys/am2pm/app/current"
	av_path = "/home/choiys/am2pm/app/av"
	all_count = len(os.listdir("/home/choiys/cuckoo/.cuckoo/storage/analyses"))-1

	vt_result = {}
	vt_scan_url = "https://www.virustotal.com/vtapi/v2/file/scan"
	vt_report_url = "https://www.virustotal.com/vtapi/v2/file/report"
	params = {'apikey': 'dcf9d3c8969c08565f0c66e80aa78cf6694d7eb249b6711fdd75ecb983ec2307'}
	for f in dlist:
		files = {'file': (f, open(dpath+f, 'rb'))}
		response = requests.post(vt_scan_url, files=files, params=params)
		params = {'apikey': 'dcf9d3c8969c08565f0c66e80aa78cf6694d7eb249b6711fdd75ecb983ec2307', 'resource': response.json()['resource']}
		response = requests.get(vt_report_url, params=params)
		vt_count = 0
		try:
			vt_json = response.json()
		except:
			print response.text
			vt_json['response_code'] = -2
		if vt_json['response_code'] == -2:
			for i in range(5):
				if vt_json['response_code'] == -2:
					time.sleep(5)
					response = requests.get(vt_report_url, params=params)
					try:
						vt_json = response.json()
					except:
						vt_json['response_code'] = -2
				else:
					break
					 
		vt_av_json = {}
		vt_total = vt_json['total']
		vt_av_list = vt_json['scans']
		for av in vt_av_list:
			vt_av_details = vt_av_list[av]
			detected = vt_av_details['detected']
			if detected == True:
				vt_count += 1
				vt_av_name = vt_av_details['result']
				vt_av_json[av] = vt_av_name
		
		vt_av_json['total'] = vt_total
		vt_av_json['count'] = vt_count
		vt_av_json['url'] = links[f]
		vt_result[f] = vt_av_json
		vt_result['url'] = links['url']

	with open(num_path, "w") as f:
		f.write(str(all_count)+'\n')
		f.write(str(len(dlist))+'\n')
		f.write(json.dumps(links))

	with open(av_path, "w") as f:
		f.write(json.dumps(vt_result))

	return render_template('index.html', submit=True, stat = stat)
