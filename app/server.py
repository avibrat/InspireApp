from flask import Flask, jsonify, request
import requests
import json
import ast
import config

app = Flask(__name__)

data_url = None
headers = {
    'Content-Type': 'application/json'
}

if config.DEVELOPMENT:
    data_url = 'https://data.{}.hasura-app.io'.format(config.PROJECT_NAME)
    headers['Authorization'] = 'Bearer ' + config.ADMIN_TOKEN
else:
    # Make a request to the data API as the admin role for full access
    data_url = 'http://data.hasura'
    headers['X-Hasura-Role'] = 'admin'
    headers['X-Hasura-User-Id'] = '1'

query_url = data_url + '/v1/query'


@app.route("/")
def hello():
	return "Hello World!"


@app.route("/signup",methods=["POST"])
def signup():
	email = request.args.get('email')
	password = request.args.get('password')
	username = request.args.get('username')
	url = query_url
	params = {
		"type":"insert",
		"args":{
			"table":"user",
			"objects":[
				{
					"email":email,
					"username":username,
					"pwd" : password
				}
			]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	return resp.text
	
@app.route("/login",methods=["POST"])
def login():
	email = request.args.get('email')
	password = request.args.get('password')
	url = query_url
	params = {
		"type":"select",
		"args":{
			"table":"user",
			"columns":["email","pwd"],
			"where": {"email" : email}
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	querylist = ast.literal_eval(resp.text)
	query_json = {}
	query_json["result"] = querylist
	resp.connection.close()
	return json.dumps(query_json)

	

if __name__ == '__main__':
    app.run(debug=True)
