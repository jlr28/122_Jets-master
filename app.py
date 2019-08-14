from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
from openpyxl import load_workbook
import os
import pickle
import csv

app = Flask(__name__)

app.secret_key = os.urandom(12)

global user

with open('static/test.csv', newline='') as csvfile:
    skedreader = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
    print(skedreader[0][9])


##Setup the Database:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Setup the sked Class / Table in the Database:

class Sked(db.Model):
    __tablename__='sked'
    id = db.Column(db.Integer, primary_key=True)
    evt = db.Column(db.Integer, nullable=True)
    callsign = db.Column(db.String(64), nullable=True)
    times = db.Column(db.String(64), nullable=True)
    aircraft = db.Column(db.String(64), nullable=True)
    aircrew = db.Column(db.String(64), nullable=True)
    mission = db.Column(db.String(64), nullable=True)
    launch = db.Column(db.String(64), nullable=True)
    out = db.Column(db.String(64), nullable=True)
    recover = db.Column(db.String(64), nullable=True)
    remarks = db.Column(db.String(512), nullable=True)

## Setup the JET Class / Table in the Database:

class Jet(db.Model):
    __tablename__ = 'jets'
    id = db.Column(db.Integer, primary_key=True)
    side = db.Column(db.Integer, index=True)
    parking = db.Column(db.Integer, default = 0)
    fuel = db.Column(db.Boolean, default = False)
    dta = db.Column(db.Boolean, default= False)
    arm = db.Column(db.Boolean, default= False)
    notes = db.Column(db.String(512), nullable=True)
    flying = db.Column(db.Boolean, default = False)
    ordnance = db.Column(db.String(64), default="")
    remarks = db.Column(db.String(512), default="")
    status = db.Column(db.Boolean, default = False)


    def __repr__(self):
        return str(self.side)

def num_spots():
    return settings['rows']*settings['per_row']

def seed_db():
    for i in range(1,20):
        new_jet = Jet(id=i, side=randint(400,700),parking=randint(1,40), fuel=choice([True,False]),
         dta=choice([True,False]),arm=choice([True,False]),flying=choice([True,False,False,False]),status=choice([True,True,True,False]))
        db.session.add(new_jet)
        db.session.commit()
    return True

def seed_sked_db():
    for j in range(len(skedreader)):
        new_event = Sked(id=j, evt=skedreader[j][0], callsign=skedreader[j][1], times=skedreader[j][2],
        aircraft=skedreader[j][3], aircrew=skedreader[j][4], mission=skedreader[j][5], launch=skedreader[j][6], out=skedreader[j][7],
        recover=skedreader[j][8], remarks=skedreader[j][9])
        db.session.add(new_event)
        db.session.commit()
    return True


def insert_jet(side_num):
    new_jet = Jet(id=Jet.query.order_by(Jet.id.desc()).first().id+1, side=side_num)
    db.session.add(new_jet)
    return None

def get_jets ():
    return Jet.query.order_by(Jet.side).all()

def get_sked ():
    sked_list = Sked.query.order_by(Sked.id).all()
    return sked_list

def fill_parking():
    jet_list = get_jets()
    park_list = []
    exists = False
    for i in range(1,num_spots()+1):
        for jet in jet_list:
            if jet.parking == i:
                exists=True
                park_list.append(jet)
                break
        if not exists:
            park_list.append({"side":"-","parking":i})
        exists = False
    return park_list

def save_settings(settings):
    with open('settings.pickle',"wb") as f:
        pickle.dump(settings,f)
    return True

def load_settings():    
    with open("settings.pickle","rb") as f:
        settings = pickle.load(f)
    return settings

def getHtml():
    text = '''{%for msg in settings.messages%}
{{msg}}{%endfor%}'''
    return render_template_string(text, settings=settings)


try: settings = load_settings()
except: settings = {'refresh':30, 'rows':3, 'per_row':8, 'msg_lines':15,
        'messages':[]}

## Make the DB table (if it hasnt been created)
#db.drop_all()
#db.create_all()
#seed_db()
#seed_sked_db()

## Only shows the cover page for the site
@app.route('/')
def hello_world():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('index.html',settings=settings)

@app.route('/schedule')
def schedule():
#    if not session.get('logged_in'):
#        return render_template('login.html')
#    else:
    return render_template('schedule.html',skeds=get_sked(), settings=settings)


@app.route('/login', methods=['GET','POST'])
def do_admin_login():
    if session.get('logged_in'):
        return redirect('/')
    else:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if request.method == 'POST':
                if (username,password) in [('ODO','eagles'),('SDO','eagles'),('MX','eagles')]:
                    session['logged_in'] = True
                    response = redirect('/')
                    response.set_cookie('username', username)
                    return response
        return get('login.html').render(username=username)


@app.route("/logout")
def logout():
    session['logged_in'] = False
    response = redirect('/')
    response.set_cookie('username','')
    return response

## Lists the parking spots available and fills in jets
@app.route('/parking')
def parking_map():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('parking.html',jets=fill_parking(),settings=settings)


@app.route('/jets', methods=['GET'])
def jet_list():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        if request.method == 'GET':
            return render_template('jets.html', jets=get_jets(),settings=settings)

@app.route('/jets/add', methods=['POST'])  
def add_jet():      
    ## Make a new jet and insert into database
    insert_jet(int(request.form.get("new_side")))
    return redirect("/jets")


@app.route("/remove/<i>",methods=['GET'])
def remove_jet(i):
    ## remove the selected jet and delete from the database
    Jet.query.filter_by(id=int(i)).delete()
    return redirect('/jets')

@app.route("/fly/<i>",methods=['GET'])
def fly_jet(i):
    ## Mark the selected jet as Flying
    Jet.query.get(int(i)).flying = True
    return redirect("/parking")

@app.route("/land/<i>",methods=['GET'])
def land_jet(i):
    ## Mark the selected jet as Flying
    Jet.query.get(int(i)).flying = False
    Jet.query.get(int(i)).fuel = False
    Jet.query.get(int(i)).arm = False
    Jet.query.get(int(i)).dta = False
    return redirect("/parking")


@app.route("/park/<i>",methods=['POST'])
def park_jet(i):
    ## Get the id of the jet that was parked and update the database
    Jet.query.get(int(request.form.get("id_landed"))).parking = int(i)
    return redirect("/parking")

@app.route("/park_edit/<i>",methods=['POST'])
def park_edit(i):
    ## Get the id and info from the parking form and update database

    print(request.form)

    if request.form.get("fuel"):
        Jet.query.get(int(i)).fuel = True
    else:
        Jet.query.get(int(i)).fuel = False
    if request.form.get("dta"):
        Jet.query.get(int(i)).dta = True
    else:
        Jet.query.get(int(i)).dta = False
    if request.form.get("arm"):
        Jet.query.get(int(i)).arm = True
    else:
        Jet.query.get(int(i)).arm = False
    if request.form.get("status"):
        Jet.query.get(int(i)).status = True
    else:
        Jet.query.get(int(i)).status = False
    Jet.query.get(int(i)).ordnance = request.form.get("ordnance")
    Jet.query.get(int(i)).remarks = request.form.get("remarks")

    return redirect("/parking")


@app.route("/jet_edit/<i>",methods=['POST'])
def jet_edit(i):
    ## Get the id and info from the parking form and update database

    print(request.form)

    if request.form.get("fuel"):
        Jet.query.get(int(i)).fuel = True
    else:
        Jet.query.get(int(i)).fuel = False
    if request.form.get("dta"):
        Jet.query.get(int(i)).dta = True
    else:
        Jet.query.get(int(i)).dta = False
    if request.form.get("arm"):
        Jet.query.get(int(i)).arm = True
    else:
        Jet.query.get(int(i)).arm = False
    if request.form.get("status"):
        Jet.query.get(int(i)).status = True
    else:
        Jet.query.get(int(i)).status = False
    
    Jet.query.get(int(i)).ordnance = request.form.get("ordnance")
    Jet.query.get(int(i)).remarks = request.form.get("remarks")
    Jet.query.get(int(i)).parking = int(request.form.get("parking"))

    return redirect("/jets")


@app.route("/message",methods=['POST'])
def add_message():
    username = request.cookies.get('username')
    ## add on new messages to the message list
    settings['messages'].append(username + ': ' +request.form.get("new_message"))
    settings['messages'] = settings['messages'][-settings['msg_lines']:]
    cur_path = request.form.get("cur_path")

    save_settings(settings)
    return redirect(cur_path)

@app.route("/message/delete",methods=['POST'])
def delete_messages():
    settings['messages']=[]
    cur_path = request.form.get("cur_path")
    save_settings(settings)
    return redirect(cur_path)
        
@app.route("/settings",methods=['GET','POST'])
def get_settings():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        if request.method == 'POST':
            for k in ['rows', 'refresh','per_row','msg_lines']:
                settings[k]=int(request.form.get(k))
            if settings['refresh']<5:
                settings['refresh']=5
            save_settings(settings)
            return redirect('/settings')
        if request.method == 'GET':
            return render_template('settings.html', settings=settings)

@app.route("/_update_messages")
def sendMessagesList():
    rendered = getHtml()
    return rendered
