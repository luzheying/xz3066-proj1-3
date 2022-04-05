#!/usr/bin/env python

"""
Columbia's COMS W4111.003 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for
from sqlalchemy import exc

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.152.219/proj1part2
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.152.219/proj1part2"
#
DATABASEURI = "postgresql://xz3066:0512@35.211.155.104/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
# #

# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print (request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close() 

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database

@app.route('/candidate', methods=['POST','GET'])
def candidate():
  if "GET" == request.method:
    return render_template("candidate.html")
  else:
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone = request.form['phone']
    if first_name == "" or last_name == "":
      return render_template("candidate.html", insertErr="First name and last name should be not null.")
    try:
      g.conn.execute (text("INSERT INTO Candidates (first_name,last_name,phone,email) VALUES (:first_name,:last_name,:phone,:email)"), {"first_name":first_name,"last_name":last_name, "email":email, "phone":phone})
      return render_template("candidate.html")
    except exc.IntegrityError as e:
      return render_template("candidate.html", insertErr="Integrity Error. Please make sure you are following the database contraint. Email should be unique. ")



@app.route('/findCandidate', methods=['GET'])
def findCandidate():
    email = request.args.get('email')
    cursor = g.conn.execute (text("SELECT * FROM Candidates WHERE email = :email"), {"email":email})
    # id = cursor.first()['id']
    res = cursor.first()
    if res == None:
      return render_template('candidate.html', searchErr="No result found.")
    applications = []
    cursorApp = g.conn.execute(text("SELECT * FROM Applications WHERE candidate_id = :candidate_id"), {"candidate_id": res.id})
    for app in cursorApp:
      cursorPos = g.conn.execute(text("SELECT * FROM Positions WHERE id = :position_id"), {"position_id": app.position_id})
      position = cursorPos.first()
      companyName = (g.conn.execute(text("SELECT name FROM Companys WHERE id = :id"), {"id":position.company_id})).first()['name']
      applications.append({"date":app.date, "time":app.time, "positionCompany":companyName, "positionName":position.name, "positionDescription":position.description, "positionLocation":position.location})
    interviews = g.conn.execute(text("SELECT * FROM interviews INNER JOIN Applications ON interviews.application_id = Applications.id WHERE candidate_id = :candidate_id"), {"candidate_id":res.id})
    events = []
    eventIDs = g.conn.execute(text("SELECT event_id FROM Attends WHERE candidate_id = :candidate_id"), {"candidate_id":res.id})
    for eid in eventIDs:
      event = (g.conn.execute(text("SELECT * FROM Events WHERE id = :id"), {"id":eid.event_id})).first()
      events.append(event)
    return render_template('candidate_home.html', candidate=res, applications=applications, events=events, interviews=interviews)

@app.route('/candidate_home')
@app.route('/candidate_home/<id>', methods=['GET'])
def candidate_home():
  print(request.args)
  return render_template('candidate_home.html')



@app.route('/host', methods=['POST','GET'])
def host():
  if "GET" == request.method:
    return render_template("host.html")
  else:
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    # print(first_name)
    organization = request.form['organization']
    if first_name == "" or last_name == "":
      return render_template("host.html", insertErr="First name and last name should be not null.")
    print(first_name)
    print(last_name)
    try:
      g.conn.execute (text("INSERT INTO Hosts (first_name,last_name,organization) VALUES (:first_name,:last_name,:organization)"), {"first_name":first_name,"last_name":last_name, "organization":organization})
      return render_template("host.html")
    except exc.IntegrityError as e:
      return render_template("host.html", insertErr="Integrity Error. Please make sure you are following the database contraint.")


@app.route('/findHost', methods=['GET'])
def findHost():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    cursor = g.conn.execute (text("SELECT * FROM Hosts WHERE first_name = :first_name AND last_name = :last_name"), {"first_name":first_name, "last_name":last_name})
    # id = cursor.first()['id']
    companys = g.conn.execute(text("SELECT id, name FROM Companys"))
    res = []
    for h in cursor:
      events = []
      eventIDs = g.conn.execute(text("SELECT event_id, budget FROM Organizes WHERE host_id = :host_id"), {"host_id":h.id})
      for eid in eventIDs:
        event = (g.conn.execute(text("SELECT * FROM Events WHERE id = :id"), {"id":eid.event_id})).first()
        events.append({"id": event.id, "date":event.date, "time":event.time, "description":event.description, "location":event.location, "budget":eid.budget})
      res.append({"id": h.id, "first_name":h.first_name, "last_name":h.last_name, "organization":h.organization, "events":events,"companys":companys})
    if len(res) == 0:
      return render_template('host.html', searchErr="No result found.")
    return render_template('host_home.html', hosts=res)


@app.route('/deleteEvent', methods=['get'])
def deleteEvent():
    id = request.args.get('event_id')
    host_id = request.args.get('host_id')
    if (g.conn.execute(text("SELECT * FROM Events WHERE id = :event_id"), {"event_id":id})).first() == None:
      return render_template("host.html", insertErr="Delete failed. Event id invalid. Event not exists.")
    g.conn.execute(text("DELETE FROM Events WHERE id = :event_id"), {"event_id":id})
    cursor = g.conn.execute (text("SELECT * FROM Hosts WHERE id = :host_id"), {"host_id":host_id})
    # id = cursor.first()['id']
    res = []
    for h in cursor:
      events = []
      eventIDs = g.conn.execute(text("SELECT event_id, budget FROM Organizes WHERE host_id = :host_id"), {"host_id":h.id})
      for eid in eventIDs:
        event = (g.conn.execute(text("SELECT * FROM Events WHERE id = :id"), {"id":eid.event_id})).first()
        events.append({"id": event.id, "date":event.date, "time":event.time, "description":event.description, "location":event.location, "budget":eid.budget})
      res.append({"id": h.id, "first_name":h.first_name, "last_name":h.last_name, "organization":h.organization, "events":events})
    if len(res) == 0:
      return render_template('host.html', searchErr="Delete failed. No result found.")
    return render_template('host_home.html', hosts=res)


@app.route('/event', methods=['post'])
def event():
    host_id = request.form.get('host_id')
    date = request.form['date']
    time = request.form['time']
    description = request.form['description']
    location = request.form['location']
    capacity = request.form['capacity']
    budget = request.form['budget']
    # print(first_name)
    if date == "":
      return render_template("host.html", insertErr="Register event failed. Date should not be null.")
    event = g.conn.execute(text("INSERT INTO events (date, time, description, location, capacity) VALUES (:date, :time, :description, :location, :capacity) RETURNING id"), {"date":date,"time":time, "description":description,"location":location,"capacity":capacity})
    event_id = event.first()[0]
    g.conn.execute(text("INSERT INTO Organizes (budget, event_id, host_id) VALUES (:budget, :event_id, :host_id)"), {"budget":budget,"event_id":event_id, "host_id":host_id})
    cursor = g.conn.execute (text("SELECT * FROM Hosts WHERE id = :host_id"), {"host_id":host_id})
  # id = cursor.first()['id']
    res = []
    for h in cursor:
      events = []
      eventIDs = g.conn.execute(text("SELECT event_id, budget FROM Organizes WHERE host_id = :host_id"), {"host_id":h.id})
      for eid in eventIDs:
        event = (g.conn.execute(text("SELECT * FROM Events WHERE id = :id"), {"id":eid.event_id})).first()
        events.append({"id": event.id, "date":event.date, "time":event.time, "description":event.description, "location":event.location, "budget":eid.budget})
      res.append({"id": h.id, "first_name":h.first_name, "last_name":h.last_name, "organization":h.organization, "events":events})
    if len(res) == 0:
      return render_template('host.html', searchErr="No result found.")
    return render_template('host_home.html', hosts=res)



@app.route('/invite', methods=['post'])
def invite():
    host_id = request.form.get('host_id')
    company_id = request.form['company_id']
    event_id = request.form['event_id']
    if (g.conn.execute(text("SELECT * FROM Companys WHERE id = :company_id"), {"company_id":company_id})).first() == None:
      return render_template("host.html", insertErr="Invite failed. Company id invalid. Company not exists.")
    if (g.conn.execute(text("SELECT * FROM Events WHERE id = :event_id"), {"event_id":event_id})).first() == None:
      return render_template("host.html", insertErr="Invite failed. Event id invalid. Event not exists.")
    g.conn.execute(text("INSERT INTO invites (event_id,host_id,company_id) VALUES (:event_id,:host_id,:company_id)"), {"company_id":company_id,"event_id":event_id, "host_id":host_id})
    cursor = g.conn.execute (text("SELECT * FROM Hosts WHERE id = :host_id"), {"host_id":host_id})
  # id = cursor.first()['id']
    res = []
    for h in cursor:
      events = []
      eventIDs = g.conn.execute(text("SELECT event_id, budget FROM Organizes WHERE host_id = :host_id"), {"host_id":h.id})
      for eid in eventIDs:
        event = (g.conn.execute(text("SELECT * FROM Events WHERE id = :id"), {"id":eid.event_id})).first()
        events.append({"id": event.id, "date":event.date, "time":event.time, "description":event.description, "location":event.location, "budget":eid.budget})
      res.append({"id": h.id, "first_name":h.first_name, "last_name":h.last_name, "organization":h.organization, "events":events})
    if len(res) == 0:
      return render_template('host.html', searchErr="No result found.")
    return render_template('host_home.html', hosts=res)



@app.route('/host_home')
@app.route('/host_home/<id>', methods=['GET'])
def host_home():
  print(request.args)
  return render_template('host_home.html')


@app.route('/company', methods=['POST','GET'])
def company():
  if "GET" == request.method:
    return render_template("company.html")
  else:
    name = request.form['name']
    description = request.form['description']
    location = request.form['location']
    if name == "":
      return render_template("company.html", insertErr="Name should be not null.")
    try:
      g.conn.execute (text("INSERT INTO Companys (name, description, location) VALUES (:name,:description,:location)"), {"name":name,"description":description, "location":location})
      return render_template("company.html")
    except exc.DataError as e:
      return render_template("company.html", insertErr="Data Error. Maybe it is because your input value is too long (check description).")

  
@app.route('/findCompany', methods=['GET'])
def findCompany():
    name = request.args.get('name')
    cursor = g.conn.execute (text("SELECT * FROM Companys WHERE name = :name"), {"name":name})
    # id = cursor.first()['id']
    res = []
    for c in cursor:
      recruiters = g.conn.execute(text("SELECT * FROM Recruiters WHERE company_id = :company_id"), {"company_id": c.id})
      positions = g.conn.execute(text("SELECT * FROM Positions WHERE company_id = :company_id"), {"company_id": c.id})
      events = g.conn.execute(text("SELECT * FROM events INNER JOIN invites ON events.id = invites.event_id WHERE invites.company_id = :company_id"), {"company_id": c.id})

      res.append({"name":c.name, "description":c.description, "location":c.location, "recruiters":recruiters, "positions":positions, "events":events})
    if len(res) == 0:
      return render_template('company.html', searchErr="No result found.")
    return render_template('company_home.html', companys=res)

@app.route('/company_home')
@app.route('/company_home/<id>', methods=['GET'])
def company_home():
  print(request.args)
  return render_template('company_home.html')


@app.route('/recruiter', methods=['POST','GET'])
def recruiter():
  if "GET" == request.method:
    companys = g.conn.execute(text("SELECT id, name FROM Companys"))
    return render_template("recruiter.html", companys=companys)
  else:
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    phone = request.form["phone"]
    email = request.form["email"]
    title = request.form["title"]
    company_id = request.form["company_id"]
    if first_name == "" or last_name == "":
      return render_template("recruiter.html", insertErr="First name and last name should be not null.")
    if (g.conn.execute(text("SELECT * FROM Companys WHERE id = :company_id"), {"company_id":company_id})).first() == None:
      return render_template("recruiter.html", insertErr="Company id invalid. Company not exists.")
    g.conn.execute (text("INSERT INTO Recruiters (first_name, last_name, company_id, phone, email, title) VALUES (:first_name, :last_name, :company_id, :phone, :email, :title)"), {"first_name":first_name, "last_name":last_name, "company_id":company_id, "phone":phone, "email":email, "title":title})
    return render_template("recruiter.html")


    
@app.route('/findRecruiter', methods=['GET'])
def findRecruiter():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    cursor = g.conn.execute (text("SELECT * FROM Recruiters WHERE first_name = :first_name AND last_name = :last_name"), {"first_name":first_name, "last_name":last_name})
    # id = cursor.first()['id']
    res = []
    for r in cursor:
      print(r.id)
      company = (g.conn.execute(text("SELECT * FROM Companys WHERE id = :id"), {"id":r.company_id})).first()
      applicationIds = g.conn.execute(text("SELECT application_id FROM Approves WHERE recruiter_id = :recruiter_id"), {"recruiter_id":r.id})
      applications = []
      for aid in applicationIds:
        app = (g.conn.execute(text("SELECT * FROM Applications WHERE id = :id"), {"id":aid.application_id})).first()
        candidate = (g.conn.execute(text("SELECT * FROM Candidates WHERE id = :id"), {"id":app.candidate_id})).first()
        position = (g.conn.execute(text("SELECT * FROM Positions WHERE id = :id"), {"id":app.position_id})).first()
        resume = ""
        if app.resume == 'Y':
          resume = "Resume submitted."
        else:
          resume = "Resume unsubmitted or unknown."
        applications.append({"date":app.date, "time":app.time, "resume":resume, "candidate":candidate, "position":position})
      interviews = g.conn.execute(text("SELECT * FROM interviews INNER JOIN Applications ON interviews.application_id = Applications.id WHERE recruiter_id = :recruiter_id"), {"recruiter_id":r.id})
      res.append({"first_name":r.first_name, "last_name":r.last_name, "title":r.title, "phone":r.phone, "email":r.email, "applications":applications, "company":company, "interviews":interviews})
    if len(res) == 0:
      return render_template('recruiter.html', searchErr="No result found.")
    return render_template('recruiter_home.html', recruiters=res)


@app.route('/recruiter_home')
@app.route('/recruiter_home/<id>', methods=['GET'])
def recruiter_home():
  print(request.args)
  return render_template('recruiter_home.html')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
