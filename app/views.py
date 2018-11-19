from flask import request
from flask import Response
from flask import render_template
from flask import redirect
from flask import session
from app import app

import os


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
