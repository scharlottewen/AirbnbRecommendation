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
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
DATABASEURI = "postgresql://yj2627:2320@104.196.152.219/proj1part2"
engine = create_engine(DATABASEURI)
conn = engine.connect()


# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#

#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


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
    print("uh oh, problem connecting to database")
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
# PROTIP: (the trailing / in the path sis important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/

@app.route('/view', methods=['GET', 'POST'])
def view():
#  print request.args
  if request.method == 'POST':
    if request.form.get("lid") and request.form.get("long"): # add new listing
#        print request.form
        lid = request.form['lid']
        long = request.form['long']
        lat = request.form['lat']
        price = request.form['price']
        rtype = request.form['rtype']
        boro = request.form['boro']
        insertListing = "INSERT INTO Airbnb_Listings (Lid, Longitude, Latitude, Price, Room_Type, Name) VALUES (" + lid + ", " + str(long) + ", " + str(lat) + ", " + str(price) + ", \'" + rtype + "\', \'" + boro + "\')"
        conn.execute(insertListing)
#        return render_template("view.html", listing = anyBR)

    elif request.form.get("lid"):
        lid = request.form['lid']
        conn.execute("DELETE FROM Airbnb_Listings WHERE lid = \'" + lid + "\'")
        
    elif request.form.get("cid"):
#        print request.form
        cid = request.form['cid']
        percent = request.form['percent']
        updateCovid = "UPDATE Covid_Info_Associated SET Percent = " + str(percent) + " WHERE Covidid = " + str(cid)
        conn.execute(updateCovid)
  
#  else:
    # general queries
  boro = "select * from Borough"
  listing = "select * from Airbnb_Listings"
  covid = "select * from Covid_Info_Associated"
  census = "select * from Census_Info_Related"
  crime = "select * from Crime_Cases_Within"
  
  list = conn.execute(listing)
  borough = conn.execute(boro)
  cov = conn.execute(covid)
  cens = conn.execute(census)
  crim = conn.execute(crime)
  return render_template("view.html", listing = list, boro = borough, covid = cov, census = cens, crime = crim)

@app.route('/', methods=['GET', 'POST'])
#@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
#  print request.args
  if request.method == 'POST':
#    print request.form
    mxprice = request.form['mxprice']
    criteria = request.form['criteria']
    roomtype = request.form['roomtype']
    
    if roomtype == 'any':
        if criteria == 'any': # select any within max price
            any = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice)
            anyBR = conn.execute(any)
            return render_template("index.html", listing = anyBR)
        if criteria == 'crime':
            crimeBoro = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.name in (SELECT B.Name FROM Borough B EXCEPT SELECT DISTINCT C1.Name FROM (SELECT C.Name, COUNT(*) AS Ct FROM Crime_Cases_Within C GROUP BY C.Name) C1 CROSS JOIN (SELECT C.Name, COUNT(*) AS Ct FROM Crime_Cases_Within C GROUP BY C.Name) C2 WHERE C1.Ct < C2.Ct)"
            crimeB = conn.execute(crimeBoro)
            return render_template("index.html", listing = crimeB)
        if criteria == 'covid':
            covidBoro = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.name in (SELECT C.Name FROM Covid_Info_Associated C EXCEPT SELECT C1.Name FROM Covid_Info_Associated C1 CROSS JOIN Covid_Info_Associated C2 WHERE C1.Percent > C2.Percent)"
            covidB = conn.execute(covidBoro)
            return render_template("index.html", listing = covidB)
        if criteria == 'census':
            censusBoro = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.name in (SELECT C.Name FROM Census_Info_Related C EXCEPT SELECT C1.Name FROM (SELECT C.Name, AVG(Unemployment_Rate) AS av FROM Census_Info_Related C GROUP BY C.Name) C1 CROSS JOIN (SELECT C.Name, AVG(Unemployment_Rate) AS av FROM Census_Info_Related C GROUP BY C.Name) C2 WHERE C1.av > C2.av)"
            censusB = conn.execute(censusBoro)
            return render_template("index.html", listing = censusB)
    if roomtype != 'any':
        if criteria == 'any':
            anyBoro = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.room_type = \'" + roomtype + "\'"
            anyB = conn.execute(anyBoro)
            return render_template("index.html", listing = anyB)
        if criteria == 'crime':
            crimeBoro2 = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.room_type = \'" + roomtype + "\' and l.name in (SELECT B.Name FROM Borough B EXCEPT SELECT DISTINCT C1.Name FROM (SELECT C.Name, COUNT(*) AS Ct FROM Crime_Cases_Within C GROUP BY C.Name) C1 CROSS JOIN (SELECT C.Name, COUNT(*) AS Ct FROM Crime_Cases_Within C GROUP BY C.Name) C2 WHERE C1.Ct < C2.Ct)"
            crimeB2 = conn.execute(crimeBoro2)
            return render_template("index.html", listing = crimeB2)
        if criteria == 'covid':
            covidBoro2 = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.room_type = \'" + roomtype + "\' and l.name in (SELECT C.Name FROM Covid_Info_Associated C EXCEPT SELECT C1.Name FROM Covid_Info_Associated C1 CROSS JOIN Covid_Info_Associated C2 WHERE C1.Percent > C2.Percent)"
            covidB2 = conn.execute(covidBoro2)
            return render_template("index.html", listing = covidB2)
        if criteria == 'census':
            censusBoro2 = "select l.lid, l.price, l.room_type, l.name from airbnb_listings l where l.price <= " + str(mxprice) + " and l.room_type = \'" + roomtype + "\' and l.name in (SELECT C.Name FROM Census_Info_Related C EXCEPT SELECT C1.Name FROM (SELECT C.Name, AVG(Unemployment_Rate) AS av FROM Census_Info_Related C GROUP BY C.Name) C1 CROSS JOIN (SELECT C.Name, AVG(Unemployment_Rate) AS av FROM Census_Info_Related C GROUP BY C.Name) C2 WHERE C1.av > C2.av)"
            censusB2 = conn.execute(censusBoro2)
            return render_template("index.html", listing = censusB2)
    
#      post_entry = models.BlogPost(date = date, title = title, post = post)
#      db.session.add(post_entry)
#      db.session.commit()
    
    return redirect("/")
  else:
    return render_template("index.html")

  #
  # example of a database query
  #
#    cursor = g.conn.execute("SELECT name FROM test")
#    names = []
#    for result in cursor:
#        names.append(result['name'])  # can also be accessed using result[0]
#    cursor.close()

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
#    listings = []
#    context = dict(data = listings)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
#    return render_template("index.html", **context)
    
  


# Example of adding new data to the database
#@app.route('/add', methods=['POST'])
#def add():
#  name = request.form['name']
#  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
#  return redirect('/')


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
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
