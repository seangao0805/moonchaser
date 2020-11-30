import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from auth import login_required, EventDAO, GroupDAO, RunnerDAO, visit, apology

# import mysql.connector

# config = {
#   'user': 'root',
#   'password': 'root!',
#   'host': '127.0.0.1',
#   'database': 'moonchaser',
#   'raise_on_warnings': True
# }

# cnx = mysql.connector.connect(**config)

# mycursor = cnx.cursor()

# cnx.close()

app = Flask(__name__)

# Ensure templates are auto reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['DEBUG'] = True


# Ensure responses aren't cached

@app.after_request
def after_request(response):
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = 0
	response.headers["Pragma"] = "no-cache"
	return response


# Configure session to use filesystem instead of signed cookies
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///moonchaser.db")


@app.route("/")
def index():
	if session.get("runner_id") is None:
		return redirect("/sign")
	else:
		return redirect("/event")
	# return render_template("event.html", event_list=event_list, member_list=event_member_list)

@app.route("/event")
# @login_required	# after test please uncomment this line.
def event():
	# for test only here
	if session.get("runner_id") is None:
		runner_id = 0
		runner = {}
	else:
		runner_id = session['runner_id']
		runner = RunnerDAO.get_runner_basic_rid(runner_id)
	# eid = 0
	eid = request.args.get('eid')
	if eid is not None:
		event = EventDAO.get_event_detail(eid, runner_id)
		if event:
			return render_template("event_detail.html", event=event, page='event', runner=runner)
		else:
			return apology("The page you asked for is invalid", 400)
	event_list = EventDAO.get_event_list_browser(runner_id)
	return render_template("event.html", event_list=event_list, page='event', runner=runner)


@app.route("/event_operation", methods=["GET", "POST"])
def event_operation():
	if request.method == 'POST':
		rid = request.form['rid']
		eid = request.form['eid']
		oper = request.form['oper']
		if oper == 'join':
			EventDAO.join_event(rid, eid)
			title = EventDAO.get_event_title(eid)
			message = "You Just Sucessfuly joined the event: " + title
			flash(message)
			url = "event?eid="+str(eid)
			return jsonify({'url': url})
		elif oper == 'leave':
			EventDAO.leave_event(rid, eid)
			title = EventDAO.get_event_title(eid)
			message = "You Just left the event: " + title
			flash(message)
			url = "event?eid="+str(eid)
			return jsonify({'url': url})
	else:
		return redirect("/sign")


@app.route("/group_operation", methods=["GET", "POST"])
def group_operation():
	if request.method == 'POST':
		rid = request.form['rid']
		gid = request.form['gid']
		oper = request.form['oper']
		if oper == 'join':
			GroupDAO.join_group(rid, gid)
			title = GroupDAO.get_group_title(gid)
			message = "You Just Sucessfuly joined the group: " + title
			flash(message)
			url = "group?gid="+str(gid)
			return jsonify({'url': url})
		elif oper == 'leave':
			GroupDAO.leave_group(rid, gid)
			title = GroupDAO.get_group_title(gid)
			message = "You Just left the group: " + title
			flash(message)
			url = "group?gid="+str(gid)
			return jsonify({'url': url})
	else:
		return redirect("/sign")


@app.route("/group")
def group():
	if session.get("runner_id") is None:
		runner_id = 0
		runner = {}
	else:
		runner_id = session['runner_id']
		runner = RunnerDAO.get_runner_basic_rid(runner_id)
	gid = request.args.get("gid")
	if gid is not None:
		group = GroupDAO.get_group_detail(gid, runner_id)
		if group:
			return render_template("group_detail.html", group=group, page="group", runner=runner)
		else:
			return apology("The page you asked for is invalid", 400)
	
	group_list = GroupDAO.get_group_list_browser(runner_id)
	return render_template("group_browser.html", group_list=group_list, page='group', runner=runner)



@app.route("/runner")
def runner():
	if session.get("runner_id") is None:
		runner_id = 0
		runner = {}
	else:
		runner_id = session['runner_id']
		runner = RunnerDAO.get_runner_basic_rid(runner_id)
	trid = request.args.get('rid')
	if trid is not None:
		t_runner = RunnerDAO.get_runner_detail(runner_id, trid)
		if t_runner['event_list']:
			return render_template("runner_detail.html", t_runner=t_runner, page="runner", runner=runner)
		else:
			return apology("The page you asked for is invalid", 400)

	if runner_id == 0:
		return redirect("/sign")
	else:
		t_runner = RunnerDAO.get_runner_detail(runner_id, runner_id)
		return render_template("runner_detail.html", t_runner=t_runner, page="runner", runner=runner)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
	runner = RunnerDAO.get_runner_basic_rid(session['runner_id'])
	
	if request.method == "POST":
		egtype = request.form['egtype']
		print(type(egtype))
		if egtype == 'event':
			event = {}
			event['title'] = request.form['title']
			event['address'] = request.form['address']
			event['date'] = request.form['date']
			event['time'] = request.form['time']
			event['description'] = request.form['description']

			if session.get('runner_id') is None:
				return jsonify({'error': 'Please log in first! The login button is on the right top corner'})

			eid = EventDAO.create_event(session['runner_id'], event)
			
			if eid == -1:
				return jsonify({'error': 'The event name you asked for creating already exists!'})

			flash("You Successfuly Created a New Event!")
			url = 'event?eid='+str(eid)
			return jsonify({'url': url, 'error': 'You Sucessfuly Created a New Event!'})
		else:
			group = {}
			group['title'] = request.form['title']
			group['location'] = request.form['location']
			group['tags'] = request.form['tags']
			group['description'] = request.form['description']

			if session.get('runner_id') is None:
				return jsonify({'error': 'Please log in first! The login button is on the right top corner'})

			gid = GroupDAO.create_group(session['runner_id'], group)
			if gid == -1:
				return jsonify({"error": "The group name you asked for creating already exists!"})
			flash("You Successfully Created a New Group!")
			url = 'group?gid='+str(gid)
			return jsonify({'url': url, 'error': 'You Sucessfuly Created a New group!'})
	else:
		egtype = request.args.get('egtype')
		if egtype == "event":
			return render_template("create.html", egtype=egtype, page='event', runner=runner)
		else:
			return render_template("create.html", egtype=egtype, page='group', runner=runner)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
	runner = RunnerDAO.get_runner_basic_rid(session['runner_id'])
	
	if request.method == "POST":
		egtype = request.form['egtype']
		if egtype == 'event':
			event = {}
			event['title'] = request.form['title']
			event['address'] = request.form['address']
			event['date'] = request.form['date']
			event['time'] = request.form['time']
			event['description'] = request.form['description']
			eid = request.form['eid']

			if session.get('runner_id') is None:
				return jsonify({'error': 'Please log in first! The login button is on the right top corner'})

			ueid = EventDAO.update_event(session['runner_id'], event, int(eid))
			print("ueid" + str(ueid))
			
			if ueid == -1:
				return jsonify({'error': 'Someone else already used this event name!'})

			flash("You Successfuly Editted your Event!")
			url = 'event?eid='+str(eid)
			return jsonify({'url': url, 'error': 'You Sucessfuly Editted your Event!'})
		else:
			group = {}
			group['title'] = request.form['title']
			group['location'] = request.form['location']
			group['tags'] = request.form['tags']
			group['description'] = request.form['description']
			gid = request.form['gid']

			print(group)
			if session.get('runner_id') is None:
				return jsonify({'error': 'Please log in first! The login button is on the right top corner'})

			ugid = GroupDAO.update_group(session['runner_id'], group, int(gid))
			print('ugid = '+ str(ugid))
			if ugid == -1:
				return jsonify({"error": "Someone else already used this group name!"})
			flash("You Successfully Editted your Group!")
			url = 'group?gid='+str(gid)
			return jsonify({'url': url, 'error': 'You Sucessfuly Editted your Group!'})
	else:
		egtype = request.args.get('egtype')
		if egtype == "event":
			eid = request.args.get('eid')
			event = {}
			event = EventDAO.get_event_edit_detail(eid)
			print(event)
			if not event:
				print('3333event')
				return apology("The page you asked for is invalid", 400)
			else:
				return render_template("edit.html", egtype=egtype, page='event', runner=runner, event=event, eid=eid)
		else:
			gid = request.args.get('gid')
			group = {}
			group = GroupDAO.get_group_edit_detail(gid)
			if not group:
				return apology("The page you asked for is invalid", 400)
			else:
				return render_template("edit.html", egtype=egtype, page='group', runner=runner, group=group, gid=gid)
		


@app.route("/sign", methods=["GET", "POST"])
def sign():
	session.clear()
	if request.method == "POST":
		return render_template("/")
	return render_template("sign.html")


@app.route("/login", methods=["POST"])
def login():
	name = request.form['name']
	password = request.form['password']

	if not name:
		return jsonify({'error': 'Missing Username!'})

	if not password:
		return jsonify({'error': 'Missing Password!'})

	# Query database for username
	rows = db.execute("SELECT * FROM runner WHERE username = :username", username = name)

	if len(rows) != 1 or not check_password_hash(rows[0]["pass"], password):
		return jsonify({"error": "Username and Password not Paired"})

	session["runner_id"] = rows[0]['rid']

	return jsonify({"url": '/'})


@app.route("/signup", methods=["POST"])
def signup():
	name = request.form['name']
	password = request.form['password']
	confirm = request.form['confirm']

	if not name:
		return jsonify({'error': 'Missing Username!'})

	if not password:
		return jsonify({'error': 'Missing Password!'})

	if not confirm:
		return jsonify({'error': 'Please Confirm your password!'})

	if password != confirm:
		return jsonify({"error": "passwords don't match!"})

	rows = db.execute("SELECT * FROM runner WHERE username = :name", name=name)
	if len(rows) == 1:
		return jsonify({"error": "User Already Exists!"})

	password_hash = generate_password_hash(password)
	avatar = "/static/img/avatar/default.jpg"
	rid = db.execute("INSERT INTO runner(username, pass, avatar) VALUES (:username, :passw, :avatar)", username=name, passw=password_hash, avatar=avatar)

	session['runner_id'] = rid

	flash("Registered")
	return jsonify({"url": "/event"})


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/sign")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


