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
			"where": where,
			"order_by" : order_by
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

def get_next_id(table,where={}):
	url = query_url
	params = {
		"type":"count",
		"args":{
			"table":table,
			"where" : where
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
	

@app.route("/postmessage",methods=["POST"])	
def post_message():
	from_user = call_appropriate_get('from_user')
	to_user = call_appropriate_get('to_user')
	from_email = call_appropriate_get('from_email')
	to_email = call_appropriate_get('to_email')
	msg_text = call_appropriate_get('msg_text')
	pid = call_appropriate_get('pid')
	cid = call_appropriate_get('cid')
	mid = get_next_id('message')
	url = query_url
	params = {
		"type":"insert",
		"args":{
			"table":"message",
			"objects":[
				{
					"mid" : mid,
					"from_user":from_user,
					"to_user":to_user,
					"from_email":from_email,
					"to_email":to_email,
					"msg_text" : msg_text,
					#Add cid pid here if varn says ok later on
					"cid" : int(cid),
					"pid" : int(pid)
				}
			]
		}
	}
	resp = requests.post(url=url, data=json.dumps(params),headers=headers)
	return insert_validate(resp.text)
	

@app.route("/profile",methods=["POST"])
def display_profile():
	email = call_appropriate_get('email')
	final_result = select_table('message',where={'to_email':email},order_by="-mid")
	final_result = json.loads(final_result)
	final_result["influence"] = get_next_id('message',{"to_email":email}) - 1
	return json.dumps(final_result)
	


##--------------------------------------END OF NON-WIT ENDPOINTS----------------------------------------------------	
	
	
	
	
##WIT CBT STARTS HERE	
#have question template as json object?
#select template bases on intent and personalize with placeholder
def getQuestions(data_dict):
    response = {}
    var = data_dict['entity']
    if var==None:
        response['validity']=False
        return response
    else:
        response['validity']=True
    
    if data_dict['intent'] == 'issue':
        issue = [
			["Why exactly do you feel "+var],
			
			["In what way is it effecting you?",
               "And does this feeling '"+var+"' change anything?"],
			
			["So what is the worst thing that can happen?",
               "How unlikely/likely is it for that to happen?",
               "Does that scare you?"],
			
			["Think about it from a third person's point of view. What does that look like?",
               "Do you agree with that?"],
			
			["Are your judgements based on feeling rather than on facts?",
               "Might this belief be a habit?",
               "Do you think you are focussing on irrelevant factors?"]
        ]
        response['que'] = issue
    else:
        incident = [
				["You mentioned '"+var+"'.What led to it?"],
				
				["How has this incident shaped you?",
                   "Are you using phrases that are extreme/exaggerated (like always,never,forever)?",
                   "How else could you react to this?"],
				
				["Do you blame yourself for it?",
                   "Does blaming others make you feel better?"],
				
				["What do you think about when you remember this incident?",
                   "Is this thought realistic?",
                   "What possible misinterpretations might you be making?"],
				
				["Is there a part of the picture you are overlooking?"]
        ]
        response['que'] = incident
    return response
        
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
        if not data['entities']:
            response['entity'] = None
        else:
            response['intent'] = data['entities']['intent'][0]['value']
            if response['intent'] == 'issue':
                e = 'emotion'
            else:
                e = 'event'
            if e not in data['entities']:
                response['entity'] = None
            else:   
                response['entity'] = data['entities'][e][0]['value']
        return response.json()
    except:
        return None
		

@app.route("/cbtsession",methods=["POST"])
def cbt_job():
    msg = call_appropriate_get('msg')
    r = getFromWit(msg)
    q = getQuestions(r)
    return (json.dumps(q))
	
	

if __name__ == '__main__':
	app.run(debug=True)
