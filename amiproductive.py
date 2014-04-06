#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
import bottle
import pymongo
import sendgrid
from urllib.parse import urlparse

bottle.debug(True)

mongo_con = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_HOST'],
                               int(os.environ['OPENSHIFT_MONGODB_DB_PORT']))

mongo_db = mongo_con[os.environ['OPENSHIFT_APP_NAME']]
mongo_db.authenticate(os.environ['OPENSHIFT_MONGODB_DB_USERNAME'],
                      os.environ['OPENSHIFT_MONGODB_DB_PASSWORD'])


# client = pymongo.MongoClient()
 
# mongo_db = client.amiproductive
# mongo_db.authenticate(os.environ['OPENSHIFT_MONGODB_DB_USERNAME'],
#                      os.environ['OPENSHIFT_MONGODB_DB_PASSWORD'],
#                      'amiproductive')

def user_find(data):
  if not data: return None
  return mongo_db.macs.find_one({ '_id': data})

def url_find(data):
  if not data: return None
  return mongo_db.traffic.find_one({ '_id': data})

# @bottle.route('/', method="POST")
# def index():
#   data = bottle.request.forms
#   if data.get('email'):
#     # check for pre existence
#     tuser = user_find(data.get('email'))
#     if tuser:
#       return bottle.template('index', result='You are already registered!')
#     else:
#       nuser = {
#         '_id': data.get('email'),
#         'pw': data.get('password')
#       }
#       userid = mongo_db.users.insert(nuser)
#       return bottle.template('welcome', result='You\'ve been signed up!', email=data.get('email'))
#   else:
#     return bottle.template('index', result=None)

@bottle.route('/')
def index():
  try:
    total_requests = mongo_db.traffic.aggregate([{ 
      '$group': { 
          '_id': None, 
          'total': { '$sum': "$count" } 
      }
    }])["result"][0]["total"]
  except IndexError:
    total_requests = 0

  try:
    good = mongo_db.users.find( {'_id' : '10:10:10:10'}, { 'good' : 1, '_id' : 0 } )[0]['good']
  except IndexError:
    good = 0

  try:
    bad = mongo_db.users.find( {'_id' : '10:10:10:10'}, { 'bad' : 1, '_id' : 0 } )[0]['bad']
  except IndexError:
    bad = 0
  
  try:
    percentage = "{0:.2f}".format((good / (good + bad)) * 100)
  except ZeroDivisionError:
    percentage = 0

  if int(percentage) < 50 and int(total_requests) > 100:
    email = 'alan.plotko@gmail.com'
    sg = sendgrid.SendGridClient('Drazard', 'sendgrid')
    message = sendgrid.Mail(to=email, subject='Your productivity has dropped!', text='Hey! We just saw your productivity drop! Get back to work!', from_email='alan.plotko@gmail.com')
    status, msg = sg.send(message)

  return bottle.template('index', mac='10:10:10:10', total_requests=int(total_requests), good=int(good), bad=int(bad), percentage=percentage)

@bottle.route('/visualize')
def visualize():
  with open(os.path.join(os.environ['OPENSHIFT_REPO_DIR'], 'static/assets/data/flare.json'), 'w') as f:
    d = {}
    d['name'] = 'visited_sites'
    d['children'] = []
    cursor = mongo_db.traffic.find({'mac' : '10:10:10:10'})
    for record in cursor: 
      d['children'].append({ 
        'name': record['_id'],
        'size': record['count']
      })
    f.write(json.dumps(d))
  return bottle.template('visualize', mac='10:10:10:10')

@bottle.route('/data', method="POST")
def data():
  return bottle.request.forms.get('data')

@bottle.route('/receiveData', method="POST")
def receiveData():
  post = bottle.request.forms
  good = ['google.com', 'stackoverflow.com']
  bad = ['facebook.com', 'reddit.com']

  if post.get('data'):
    files = (".png", ".jpg", ".gif", ".js")
    if any(s in post.get('data') for s in files):
      return

    try:
      url = re.search("(?P<url>https?://[^\s]+)", post.get('data')).group("url")
    except AttributeError:
      return

    if not user_find('10:10:10:10'):
      user = {
        '_id' : '10:10:10:10',
        'good' : 0,
        'bad' : 0
      }
      userId = mongo_db.users.insert(user)      

    if url is not None:   
      url = urlparse(url)[1]
    if 'www.' in url:
      url = url.replace("www.", "")
    
    if url in good:
      mongo_db.users.update(
        { '_id' : '10:10:10:10' },
        { '$inc' : { 'good' : 1 } }
      )
    elif url in bad:
      mongo_db.users.update(
        { '_id' : '10:10:10:10' },
        { '$inc' : { 'bad' : 1 } }
      )

    traffic = url_find(url)
    if traffic:
      mongo_db.traffic.update(
        { '_id' : url },
        { '$inc' : { 'count' : 1 } }
      )
    else:
      connection = {
        '_id' : url,
        'count' : 1,
        'mac' : '10:10:10:10'
      }
      new_url = mongo_db.traffic.insert(connection)

# @bottle.route('/receiveMac', method="POST")
# def receiveMac():
#   post = bottle.request.forms
#   if post.get('info'):
#     mac = post.get('info').split(" ")[1]
#     ip = post.get('info').split(" ")[2] 
#     if not user_find(mac):
#       user = {
#         '_id' : mac,
#         'ip' : ip
#       }
#       userid = mongo_db.macs.insert(user)
#     else:
#       mongo_db.macs.update(
#         { '_id' : mac },
#         { '$set' : { 'ip' : ip } }
#       )


# def snippet_create(user, code):
#   nsnippet = {
#     '_id': uuid.uuid4().hex,
#     'uid': user['_id'],
#     'code': code
#     }
#   mongo_db.snippets.insert(nsnippet)
#   return nsnippet

# def note_create(snip, user, text):
#   nnote = {
#     '_id': uuid.uuid4().hex,
#     'uid': user['_id'],
#     'cid': snip['_id'],
#     'text': text
#   }
#   mongo_db.notes.insert(nnote)

# def annote_create(snip, user, text):
#   nannote = {
#     '_id': uuid.uuid4().hex,
#     'uid': user['_id'],
#     'cid': snip['_id'],
#     'text': text
#   }
#   mongo_db.notes.insert(nannote)

# def user_list():
#   l = []
#   for u in mongo_db.users.find():
#     l.append(u['_id'])
#   l.sort()
#   return l

# def snippet_list(user):
#   l = []
#   for s in mongo_db.snippets.find():
#       if s['uid'] == user:
#         l.append(s)
#   l.sort()
#   return l

# def note_list(snippet):
#   l = []
#   for n in mongo_db.notes.find():
#     if n['cid'] == snippet:
#       l.append(n)
#   l.sort()
#   return l

# def annote_list(snippet):
#   l = []
#   for a in mongo_db.annotes.find():
#     if a['cid'] == snippet:
#       l.append(a)
#   l.sort()
#   return l

# def user_auth(user, pw):
#   if not user: return False
#   return user['pw'] == pw

# def snippet_find_by_id(snip_id):
#   if not snip_id: return None
#   return mongo_db.snippets.find_one({ '_id': snip_id})

# reserved_usernames = 'home signup login logout post static DEBUG note annote'

bottle.TEMPLATE_PATH.append(os.path.join(os.environ['OPENSHIFT_REPO_DIR'], 'views'))

# def get_session():
#   session = bottle.request.get_cookie('session', secret='secret')
#   return session

# def save_session(uid):
#   session = {}
#   session['uid'] = uid
#   session['sid'] = uuid.uuid4().hex
#   bottle.response.set_cookie('session', session, secret='secret')
#   return session

# def invalidate_session():
#   bottle.response.delete_cookie('session', secret='secret')
#   return

# @bottle.route('/dashboard')
# def dashboard():
#   session = get_session()
#   if not session: bottle.redirect('/login')
#   luser = user_find(session['uid'])
#   if not luser: bottle.redirect('/logout')
  
#   # bottle.TEMPLATES.clear()
#   return bottle.template('dashboard',
#                          # postlist=postlist,
#                          # userlist=user_list(),
#                          page='dashboard',
#                          username=luser['_id'],
#                          logged=True)

# @bottle.route('/snippets', method="POST")
# def post_snippet():
#   session = get_session()
#   luser = user_find(session['uid'])
#   if not luser: bottle.redirect('/logout')  
#   # bottle.TEMPLATES.clear()
#   data = bottle.request.forms
#   if data.get('code'):
#     snip = snippet_create(luser, data.get('code'))
#     bottle.redirect('/snippets/' + str(snip['_id']))

# @bottle.route('/snippets/<id>')
# def snippet_page(id):
#     session = get_session()
#     luser = user_find(session['uid'])
#     if not luser: bottle.redirect('/logout')
#     snippet = snippet_find_by_id(id)
#     if not snippet:
#         return bottle.HTTPError(code=404, message='snippet not found')
#     return bottle.template('snips',
#                             author=snippet['uid'],
#                             snip_id=id,
#                             snippet=snippet,
#                             code=snippet['code'],
#                             page='snips',
#                             annotes=annote_list(snippet),
#                             notes=note_list(snippet),
#                             logged=(session != None))

# @bottle.route('/note/<snip>', method='POST')
# def note(snip):
#   session = get_session()
#   if not session: bottle.redirect('/login')
#   luser = user_find(session['uid'])
#   if not luser: bottle.redirect('/logout')
#   if 'text' in bottle.request.POST:
#     text = bottle.request.POST['text']
#     note_create(snip, luser, text)

# @bottle.route('/annote/<snip>', method='POST')
# def annote(snip):
#   session = get_session()
#   if not session: bottle.redirect('/login')
#   luser = user_find(session['uid'])
#   if not luser: bottle.redirect('/logout')
#   if 'text' in bottle.request.POST:
#     text = bottle.request.POST['text']
#     annote_create(snip, luser, text)

# # @bottle.route('/signup')
# @bottle.route('/login')
# def get_login():
#   session = get_session()
#   # bottle.TEMPLATES.clear()
#   if session: bottle.redirect('/dashboard')
#   return bottle.template('login',
# 			 page='login',
# 			 error_login=False,
# 			 error_signup=False,
# 			 logged=False)

# @bottle.route('/login', method='POST')
# def post_login():
#   if 'email' in bottle.request.POST and 'password' in bottle.request.POST:
#     email = bottle.request.POST['email']
#     password = bottle.request.POST['password']
#     user = user_find(email)
#     if user_auth(user, password):
#       save_session(user['_id'])
#       bottle.redirect('/dashboard')
#   return bottle.template('login',
# 			 page='login',
# 			 error_login=True,
# 			 error_signup=False,
# 			 logged=False)

# @bottle.route('/logout')
# def logout():
#   invalidate_session()
#   bottle.redirect('/')

# @bottle.route('/signup', method='POST')
# def post_signup():
#   if 'name' in bottle.request.POST and 'password' in bottle.request.POST:
#     name = bottle.request.POST['name']
#     password = bottle.request.POST['password']
#     if name not in reserved_usernames.split():
#       userid = user_create(name, password)
#       if userid:
#         save_session(userid)
#         bottle.redirect('/home')
#     return bottle.template('login',
# 			   page='login',
# 			   error_login=False,
# 			   error_signup=True,
# 			   logged=False)

@bottle.route('/DEBUG/cwd')
def dbg_cwd():
  return "<tt>cwd is %s</tt>" % os.getcwd()

@bottle.route('/DEBUG/env')
def dbg_env():
  env_list = ['%s: %s' % (key, value)
              for key, value in sorted(os.environ.items())]
  return "<pre>env is\n%s</pre>" % '\n'.join(env_list)

@bottle.route('/static/assets/<filename:path>', name='static')
def static_file(filename):
  return bottle.static_file(filename, root=os.path.join(os.environ['OPENSHIFT_REPO_DIR'], 'static/assets'))

application = bottle.default_app()
