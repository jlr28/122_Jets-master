from flask import Flask, render_template, render_template_string, request, redirect
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
import os
import pickle

app = Flask(__name__)


##Setup the Database:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
        new_jet = Jet(id=i, side=randint(400,700),parking=randint(1,num_parking_spots), fuel=choice([True,False]),
        dta=choice([True,False]),arm=choice([True,False]),flying=choice([True,False,False,False]),status=choice([True,True,True,False]))
        db.session.add(new_jet)
        db.session.commit()
    return True

def insert_jet(side_num):
    new_jet = Jet(id=Jet.query.order_by(Jet.id.desc()).first().id+1, side=side_num)
    db.session.add(new_jet)
    return None

def get_jets ():
    return Jet.query.order_by(Jet.side).all()

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
                <p class="my-2 p-0">{{msg}}</p>
                {%endfor%}'''
    return render_template_string(text, settings=settings)


try: settings = load_settings()
except: settings = {'refresh':30, 'rows':3, 'per_row':8, 'msg_lines':15,
        'messages':[]}

## Make the DB table (if it hasnt been created)
#db.drop_all()
#db.create_all()
#seed_db()


## Only shows the cover page for the site
@app.route('/')
@app.route('/schedule')
def hello_world():
    return render_template('index.html',settings=settings)

## Lists the parking spots available and fills in jets
@app.route('/parking')
def parking_map():
    return render_template('parking.html',jets=fill_parking(),settings=settings)


@app.route('/jets', methods=['GET'])
def jet_list():
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
    ## add on new messages to the message list
    settings['messages'].append(request.form.get("new_message"))
    settings['messages'] = settings['messages'][-settings['msg_lines']:]
    cur_path = request.form.get("cur_path")
    save_settings(settings)
    return redirect(cur_path)

@app.route("/message/delete",methods=['POST'])
def delete_messages():
    ## add on new messages to the message list
    settings['messages']=[]
    cur_path = request.form.get("cur_path")
    save_settings(settings)
    return redirect(cur_path)
        
@app.route("/settings",methods=['GET','POST'])
def get_settings():
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
