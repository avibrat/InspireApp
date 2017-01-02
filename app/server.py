from flask import Flask, jsonify, request
import requests
import json
import ast
from wit import Wit
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


android_test = True


def call_appropriate_get(parameter):
	if android_test == True:
		return request.form.get(parameter)
	else:
		return request.args.get(parameter)



@app.route("/",methods=["POST"])
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

def select_table(table,where={},order_by=""):
	url = query_url
	params = {
		"type":"select",
		"args":{
			"table":table,
			"columns":["*"],
			"where":where,
			"order-by" : order_by
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	querylist = ast.literal_eval(resp.text)
	post_result = {}
	post_result["result"] = querylist
	return json.dumps(post_result)

@app.route("/solutionfeed",methods=["POST"])
def get_posts():
	return select_table("user_posts",{},"-pid")

def get_next_id(table):
	url = query_url
	params = {
		"type":"count",
		"args":{
			"table":table,
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
	pid = get_next_id("user_posts")
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


@app.route("/cheerfeed",methods=["POST"])
def cheerfeed():
	return select_table("cheerfeed",{},"-chid")

@app.route("/makecheerpost",methods=["POST"])
def make_cheer_post():
	username = call_appropriate_get('username')
	email = call_appropriate_get('email')
	post_text = call_appropriate_get('post_text')
	date = call_appropriate_get('date')
	type = call_appropriate_get('type')
	image_url = call_appropriate_get('image_url')
	chid = get_next_id("cheerfeed")
	url = query_url
	params = {
		"type":"insert",
		"args":{
			"table":"cheerfeed",
			"objects":[
				{
					"chid":chid,
					"email":email,
					"username" : username,
					"post_text" : post_text,
					"date" : date,
					"image_url" : image_url,
					"type" : type
				}
			]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	return insert_validate(resp.text)
	

@app.route("/postcomment",methods=["POST"])
def post_comment():
	username = call_appropriate_get('username')
	email = call_appropriate_get('email')
	comment_text = call_appropriate_get('comment_text')
	date = call_appropriate_get('date')
	pid = call_appropriate_get('pid')
	cid = get_next_id('comment')
	url = query_url
	params = {
		"type":"insert",
		"args":{
			"table":"comment",
			"objects":[
				{
					"cid":cid,
					"pid":int(pid),
					"email":email,
					"username" : username,
					"comment_text" : comment_text,
					"date" : date
				}
			]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	return insert_validate(resp.text)
	
@app.route('/displaycomment',methods=["POST"])
def display_comment():
	pid = call_appropriate_get('pid')
	return select_table('comment',{"pid":int(pid)},"-cid")
	

	
	
	
	
	
	
	
	
	
	
##WIT CBT STARTS HERE	
#have question template as json object?
issue = {
    'q1': "Why exactly do you feel",
    'q2': "In what way is it effecting you?",
    'q3': "And does you being like this change anything?",
    'q4': "So what is the worst thing that can happen?",
    'q5': "How unlikely/likely is it for that to happen?",
    'q6': "Does that scare you?",
    'q7': "Think about it from a third person's point of view. What does that look like?"
}
incident = {
    'q1': "You mentioned ",
    'q2': "How has this incident shaped you?",
    'q3': "How else could you react to this?"
}




#get template and personalize it with entity
def getQuestions(var,template):
    post = ""
    if template == incident:
        post = ". What led to it"
    template['q1'] = template['q1'] + var + post +"?"
    return template
        
#based on intent pick question template
def getTemplate(datadict):
    if datadict['intent'] == 'issue':
        template = issue
    else:
        template = incident
    var = datadict['entity']
    return var,template

#get msg from user and pass msg to wit and get intent and entity
def getFromWit(msg):
    p = {
         'v':'20160813',
         'q': msg
        }
    h = {'Authorization':"Bearer NOMO6NVDPVVX3EAX65LZAZ2ROXLVGUVN"}
    url = 'https://api.wit.ai/message'
    d = requests.post(url,headers=h,params=p)
    data = d.json()
    response = {}
    try:
        #if entitiy not present send notEnoughData
        response['intent'] = data['entities']['intent'][0]['value']
        if response['intent'] == 'issue':
            e = 'emotion'
        else:
            e = 'event'
        response['entity'] = data['entities'][e][0]['value']
        print(response)
        return response
    except:
        return None

@app.route("/cbtsession",methods=["POST"])
def cbt_job():
    msg = call_appropriate_get('msg')
    r = getFromWit(msg)
    v,t = getTemplate(r)
    q = getQuestions(v,t)
    return (json.dumps(q,sort_keys=True))
	
	

if __name__ == '__main__':
	app.run(debug=True)
