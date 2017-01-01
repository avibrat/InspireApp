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


android_test = False


def call_appropriate_get(parameter):
	if android_test == True:
		return request.form.get(parameter)
	else:
		return request.args.get(parameter)



@app.route("/")
def hello():
	return "Hello World!"


def insert_validate(text):
	resp_json = json.loads(text)
	final_result = {}
	final_result["error"] = None

	if "affected_rows" in resp_json:
		final_result["validity"] = True
	else:
		final_result["validity"] = False
		final_result["error"] = resp_json["error"]
	return json.dumps(final_result)
	

@app.route("/signup",methods=["POST"])
def signup():
	email = call_appropriate_get('email')
	password = call_appropriate_get('password')
	username = call_appropriate_get('username')
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
	return insert_validate(resp.text)
	
@app.route("/login",methods=["POST"])
def login():
	email = call_appropriate_get('email')
	password = call_appropriate_get('password')
	url = query_url
	params = {
		"type":"select",
		"args":{
			"table":"user",
			"columns":["*"],
			"where": {"email" : email}
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	querylist = ast.literal_eval(resp.text)
	query_json = {}
	if len(querylist) == 1 and querylist[0]["pwd"] == password:
		query_json["validity"] = True
		query_json["username"] = querylist[0]["username"]
	else:
		query_json["validity"] = False
		query_json["username"] = None
	
	query_json["status"] = resp.status_code
	query_json["gottten_email"] = email
	query_json["gotten_password"] = password
	resp.connection.close()
	return json.dumps(query_json)	

def select_table(table):
	url = query_url
	params = {
		"type":"select",
		"args":{
			"table":table,
			"columns":["*"]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	querylist = ast.literal_eval(resp.text)
	post_result = {}
	post_result["result"] = querylist
	return post_result

@app.route("/solutionfeed",methods=["POST"])
def get_posts():
	return json.dumps(select_table("user_posts"))

def get_next_id():
	url = query_url
	params = {
		"type":"count",
		"args":{
			"table":"user_posts",
			"where" : {}
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	result = json.loads(resp.text)["count"] + 1
	return result
	
@app.route("/makesolutionpost",methods=["POST"])
def make_solution_post():
	username = call_appropriate_get('username')
	email = call_appropriate_get('email')
	post_text = call_appropriate_get('post_text')
	date = call_appropriate_get('date')
	pid = get_next_id()
	url = query_url
	params = {
		"type":"insert",
		"args":{
			"table":"user_posts",
			"objects":[
				{
					"pid":pid,
					"email":email,
					"username" : username,
					"post_text" : post_text,
					"date" : date
				}
			]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	return insert_validate(resp.text)


@app.route("/cheerfeed")
def cheerfeed():
	return json.dumps(select_table("cheerfeed"))
	
if __name__ == '__main__':
    app.run(debug=True)
