from flask import request
from flask import Response
from flask import render_template
from flask import redirect
from flask import session
from app import app


@app.route('/')
def main():
	return render_template('index.html')
