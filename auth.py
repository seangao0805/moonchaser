import os
import requests
import urllib.parse
from cs50 import SQL

from flask import redirect, render_template, request, session
from functools import wraps
import sqlite3
from sqlite3 import Error

db = SQL("sqlite:///moonchaser.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("runner_id") is None:
            return redirect("/sign")
        return f(*args, **kwargs)
    return decorated_function


def get_runner_avatar(id):
    rows = db.execute("SELECT * FROM runner WHERE rid = :rid", rid=id)
    return rows[0]['avatar']

# import sqlite3
# from sqlite3 import Error


class sqlInterface:
    def create_connection(db_file='moonchaser.db'):
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)

        return conn
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    def dict_sql_connection(db_file="moonchaser.db"):
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
                print(e)

        conn.row_factory = sqlInterface.dict_factory
        return conn

    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """

class EventDAO:
    def get_event_list_browser(rid=0, limit=24, start=0):
        event_lists = []

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT eid, title, owner, pdate, ptime, location, logo, description FROM event WHERE privacy<? ORDER BY eid DESC LIMIT ?", (6, limit,))
        rows = cur.fetchall()
    
        # print(rows)
        for row in rows:
            event = {} 
            eid = row['eid']
            event['url'] = "event?eid="+str(eid)
            event['title'] = row['title']
            event['logo'] = row['logo']
            event['alt'] = row['title']
            event['description'] = row['description']
            event['ptime'] = row['pdate'] + " " + row['ptime']
            event['location'] = row['location']
            event['action'] = {}
            role = RunnerDAO.get_event_role_rid(rid, eid)
            # print('rid = '+str(rid)+', eid = '+str(eid)+', role = ' + str(role))
            if role == Role.Visitor:
                if rid == 0:
                    event['action'] = {'func': 'visit("/sign")', 'class':'guest', 'name':'Not Logged In'}
                else:
                    event['action'] = {'func': "event_oper("+str(rid)+","+str(eid)+","+"'join')", "class":'join', 'name':'Join'}
            elif role == Role.Owner:
                event['action'] = {'func': 'visit("event?eid='+str(eid)+'")', 'class':'owner', 'name':'My Event'}
            elif role == Role.Member:
                event['action'] = {'func': 'visit("event?eid='+str(eid)+'")', 'class':'member', 'name':'Already In'}

            # get creator information
            event['owner'] = RunnerDAO.get_runner_basic_rid(row['owner'])

            event_lists.append(event)

        #====== for test only ======
        # for events in event_lists:
        #     print(events)
        #====== for test only ======

        conn.commit()
        conn.close()

        return event_lists

    def get_event_detail(eid, rid=0):
        event = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, owner, pdate, ptime, location, logo, description FROM event WHERE eid = ? AND privacy < ? LIMIT 1", (eid, 6,))
        rows = cur.fetchall()

        if len(rows) != 1:
            return event
        row = rows[0]
        event['url'] = "event?eid="+str(eid)
        event['title'] = row['title']
        event['img'] = row['logo']
        event['alt'] = row['title']
        event['description'] = row['description']
        event['time'] = row['pdate'] + " " + row['ptime']
        event['location'] = row['location']
        event['action'] = []
        role = RunnerDAO.get_event_role_rid(rid, eid)
            # print('rid = '+str(rid)+', eid = '+str(eid)+', role = ' + str(role))
        if role == Role.Visitor:
            if rid == 0:
                action = {'func': 'visit("/sign")', 'class':'guest', 'name':'Not Logged In'}
                event['action'].append(action)
            else:
                action = {'func': "event_oper("+str(rid)+","+str(eid)+","+"'join')", "class":'join', 'name':'Join'}
                event['action'].append(action)
        elif role == Role.Owner:
            action_1 = {'func': 'visit("event?eid='+str(eid)+'")', 'class':'owner', 'name':'My Event'}
            event['action'].append(action_1)
            action_2 = {'func': "event_oper("+str(rid)+","+str(eid)+","+"'edit')", "class":'edit', 'name':'Edit'}
            event['action'].append(action_2)
        elif role == Role.Member:
            action_1 = {'func': 'visit("event?eid='+str(eid)+'")', 'class':'member', 'name':'Already In'}
            event['action'].append(action_1)
            action_2 = {'func': "event_oper("+str(rid)+","+str(eid)+","+"'leave')", "class":'member leave', 'name':'leave'}
            event['action'].append(action_2)

        event['member_list'] = EventDAO.get_event_members_detail(eid)
        event['more'] = 0
        member_list_count = len(event['member_list'])
        if member_list_count > 3:
            event['more'] = member_list_count - 3
        event['creator'] = RunnerDAO.get_runner_basic_rid(row['owner'])

        conn.commit()
        conn.close()
        
        return event

    def get_event_edit_detail(eid, rid=0):
        event = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, owner, pdate, ptime, location, logo, description FROM event WHERE eid = ? AND privacy < ? LIMIT 1", (eid, 6,))
        rows = cur.fetchall()

        if len(rows) != 1:
            return event
        row = rows[0]
        event['url'] = "event?eid="+str(eid)
        event['title'] = row['title']
        event['img'] = row['logo']
        event['alt'] = row['title']
        event['description'] = row['description']
        event['pdate'] = row['pdate']
        event['ptime'] = row['ptime']
        event['location'] = row['location']

        conn.commit()
        conn.close()
        
        return event

    def get_event_member_list(eid):
        member_list = []

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT rid FROM runner2event WHERE eid = ? AND role = ?", (eid, Role.Member,))
        rows = cur.fetchall()

        if len(rows) != 0:
            for row in rows:
                member_list.append(row['rid'])

        conn.commit()
        conn.close()
        return member_list


    def get_event_members_detail(eid):
        members = []
        member_list = []
        member_list = EventDAO.get_event_member_list(eid)

        for id in member_list:
            member = {}
            member = RunnerDAO.get_runner_basic_rid(id)
            members.append(member)

        return members


    def get_eid_list_runner(rid):
        event_ids = []
        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        role = Role.Member
        cur.execute("SELECT eid FROM runner2event WHERE rid = ? AND role >= ? ORDER BY mtime DESC LIMIT 1000", (rid, role,))
        rows = cur.fetchall()

        for row in rows:
            event_ids.append(row['eid'])

        conn.commit()
        conn.close()

        return event_ids


    def get_event_basic_eid(eid):
        event = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, logo FROM event WHERE eid = ? AND privacy < ? LIMIT 1", (eid, 6,))
        rows = cur.fetchall()

        row = rows[0]
        event['url'] = "event?eid="+str(eid)
        event['title'] = row['title']
        event['img'] = row['logo']
        event['alt'] = row['title']
        
        conn.commit()
        conn.close()

        return event

    def create_event(rid, event):
        eid = -1
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE title = ?", (event['title'],))
        rows = cur.fetchall()

        if len(rows) == 1:
            return eid
        
        # add new event to event table
        event['logo'] = "/static/img/event/default_1.jpg"
        cur.execute("INSERT INTO event(title, owner, pdate, ptime, location, logo, description, verify, privacy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", \
            (event['title'], rid, event['date'], event['time'], event['address'], event['logo'], event['description'], 1, 5,))
        eid = cur.lastrowid
        conn.commit()

        if eid != -1:
            cur.execute("INSERT INTO runner2event(rid, eid, role) VALUES (?, ?, ?)", (rid, eid, 5,))
            conn.commit()

        conn.close()
        return eid


    def update_event(rid, event, eid):
        ueid = -1
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE title = ? AND eid <> ? ", (event['title'], eid,))
        rows = cur.fetchall()

        if len(rows) == 1:
            return ueid
        
        # update event table
        cur.execute("UPDATE event SET title = ?, pdate = ?, ptime = ?, location = ?, description = ? WHERE eid = ?", \
            (event['title'], event['date'], event['time'], event['address'], event['description'], eid,))
        conn.commit()
        conn.close()

        return eid
    

    def join_event(rid, eid):
        role = Role.Member
        RunnerDAO.set_event_role(rid, eid, role)

    def leave_event(rid, eid):
        role = Role.Visitor
        RunnerDAO.set_event_role(rid, eid, role)

    def get_event_title(eid):
        title = ""
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT title FROM event WHERE eid = ? LIMIT 1", (eid,))
        rows = cur.fetchall()
        if len(rows) != 0:
            title = rows[0][0]
        conn.commit()
        conn.close()
        return title

        
def select_all_events():
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    EventDAO.get_event_list_browser()


class GroupDAO:
    def get_group_list_browser(rid=0, limit=24, start=0):
        group_lists = []

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT gid, title, owner, logo, description FROM community WHERE privacy<? ORDER BY gid DESC LIMIT ?", (6, limit,))
        rows = cur.fetchall()
    
        for row in rows:
            group = {} 
            gid = row['gid']
            group['url'] = "group?gid="+str(gid)
            group['title'] = row['title']
            group['logo'] = row['logo']
            group['alt'] = row['title']
            group['description'] = row['description']
            group['action'] = {}
            role = RunnerDAO.get_group_role_rid(rid, gid)
            member_list = GroupDAO.get_group_member_list(gid)

            if role == Role.Visitor:
                if rid == 0:
                    group['action'] = {'func': 'visit("/sign")', 'class':'guest', 'name':'Not Logged In'}
                else:
                    group['action'] = {'func': "group_oper("+str(rid)+","+str(gid)+","+"'join')", "class":'join', 'name':'Join'}
            elif role == Role.Owner:
                group['action'] = {'func': 'visit("group?gid='+str(gid)+'")', 'class':'owner', 'name':'My Group'}
            elif role == Role.Member:
                group['action'] = {'func': 'visit("group?gid='+str(gid)+'")', 'class':'member', 'name':'Mermber'}

            # get creator information
            group['owner'] = RunnerDAO.get_runner_basic_rid(row['owner'])
            group['member_count'] = len(member_list)

            group_lists.append(group)

        conn.commit()
        conn.close()

        return group_lists

    def get_group_member_list(gid):
        member_list = []

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT rid FROM runner2group WHERE gid = ? AND role >= ?", (gid, Role.Member,))
        rows = cur.fetchall()

        if len(rows) != 0:
            for row in rows:
                member_list.append(row['rid'])

        conn.commit()
        conn.close()
        return member_list


    def get_group_detail(gid, rid=0):
        group = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, owner, logo, description FROM community WHERE gid = ? AND privacy < ? LIMIT 1", (gid, 6,))
        rows = cur.fetchall()

        if len(rows) != 1:
            return group

        row = rows[0]
        group['url'] = "group?gid="+str(gid)
        group['title'] = row['title']
        group['img'] = row['logo']
        group['alt'] = row['title']
        group['description'] = row['description']
        group['action'] = []
        
        role = RunnerDAO.get_group_role_rid(rid, gid)
        if role == Role.Visitor:
            if rid == 0:
                action = {'func': 'visit("/sign")', 'class':'guest', 'name':'Not Logged In'}
                group['action'].append(action) 
            else:
                action = {'func': "group_oper("+str(rid)+","+str(gid)+","+"'join')", "class":'join', 'name':'Join'}
                group['action'].append(action) 
        elif role == Role.Owner:
            action_1 = {'func': 'visit("group?gid='+str(gid)+'")', 'class':'owner', 'name':'My Group'}
            group['action'].append(action_1)
            action_2 = {'func': "group_oper("+str(rid)+","+str(gid)+","+"'edit')", "class":'edit', 'name':'Edit'}
            group['action'].append(action_2)
        elif role == Role.Member:
            action_1 = {'func': 'visit("group?gid='+str(gid)+'")', 'class':'member', 'name':'Member'}
            group['action'].append(action_1)
            action_2 = {'func': "group_oper("+str(rid)+","+str(gid)+","+"'leave')", "class":'leave', 'name':'Leave'}
            group['action'].append(action_2)

        group['member_list'] = GroupDAO.get_group_members_detail(gid)
        group['more'] = 0
        member_list_count = len(group['member_list'])
        # if member_list_count > 3:
        #     group['more'] = member_list_count - 3
        group['creator'] = RunnerDAO.get_runner_basic_rid(row['owner'])

        conn.commit()
        conn.close()
        
        return group



    def get_gid_list_runner(rid):
        group_ids = []
        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        role = Role.Member
        cur.execute("SELECT gid FROM runner2group WHERE rid = ? AND role >= ? ORDER BY mtime DESC LIMIT 1000", (rid, role,))
        rows = cur.fetchall()

        for row in rows:
            group_ids.append(row['gid'])

        conn.commit()
        conn.close()

        return group_ids


    def get_group_basic_gid(gid):
        group = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, logo FROM community WHERE gid = ? AND privacy < ? LIMIT 1", (gid, 6,))
        rows = cur.fetchall()

        row = rows[0]
        group['url'] = "group?gid="+str(gid)
        group['title'] = row['title']
        group['img'] = row['logo']
        group['alt'] = row['title']
        
        conn.commit()
        conn.close()

        return group

    def get_group_edit_detail(gid, rid=0):
        group = {}

        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, description FROM community WHERE gid = ? AND privacy < ? LIMIT 1", (gid, 6,))
        rows = cur.fetchall()

        if len(rows) != 1:
            return group
        row = rows[0]
        group['url'] = "group?gid="+str(gid)
        group['title'] = row['title']
        group['description'] = row['description']

        conn.commit()
        conn.close()
        
        return group


    def get_group_members_detail(gid):
        members = []
        member_list = []
        member_list = GroupDAO.get_group_member_list(gid)

        for id in member_list:
            member = {}
            member = RunnerDAO.get_runner_basic_rid(id)
            members.append(member)

        return members


    def get_group_title(gid):
        title = ""
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT title FROM community WHERE gid = ? LIMIT 1", (gid,))
        rows = cur.fetchall()
        if len(rows) != 0:
            title = rows[0][0]
        
        conn.commit()
        conn.close()
        
        return title


    def create_group(rid, group):
        gid = -1
        conn = sqlInterface.create_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM community WHERE title = ?", (group['title'],))
        rows = cur.fetchall()

        if len(rows) == 1:
            return gid
        
        # add new group to group table
        group['logo'] = "/static/img/group/default.jpg"
        cur.execute("INSERT INTO community(title, owner, logo, description, verify, privacy) VALUES (?, ?, ?, ?, ?, ?)", \
            (group['title'], rid, group['logo'], group['description'], 1, 5,))
        gid = cur.lastrowid
        conn.commit()

        if gid != -1:
            cur.execute("INSERT INTO runner2group(rid, gid, role) VALUES (?, ?, ?)", (rid, gid, 5,))
            conn.commit()

        conn.close()
        return gid


    def update_group(rid, group, gid):
        ugid = -1
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM community WHERE title = ? AND gid <> ? ", (group['title'], gid,))
        rows = cur.fetchall()

        if len(rows) == 1:
            return ugid
        
        # update group table
        cur.execute("UPDATE community SET title = ?, description = ? WHERE gid = ?", \
            (group['title'], group['description'], gid,))
        conn.commit()
        conn.close()

        return gid


    def join_group(rid, gid):
        role = Role.Member
        RunnerDAO.set_group_role(rid, gid, role)

    def leave_group(rid, gid):
        role = Role.Visitor
        RunnerDAO.set_group_role(rid, gid, role)


class RunnerDAO:
    def get_event_role_rid(rid, eid):
        role = Role.Visitor
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT role FROM runner2event WHERE rid = ? AND eid = ? LIMIT 1", (rid, eid,))
        rows = cur.fetchall()
        if len(rows) != 0:
            role = rows[0][0]
        conn.commit()
        conn.close()

        return role

    def get_group_role_rid(rid, gid):
        role = Role.Visitor
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("SELECT role FROM runner2group WHERE rid = ? AND gid = ? LIMIT 1", (rid, gid,))
        rows = cur.fetchall()
        if len(rows) != 0:
            role = rows[0][0]
        conn.commit()
        conn.close()

        return role


    def get_runner_basic_rid(rid):
        person = {'url':'', \
                  'image':'', \
                  'image_large':'', \
                  'alt':'', \
                  'title':'' \
                  }

        # get person basic info from database table runner
        conn = sqlInterface.dict_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, avatar FROM runner WHERE rid = ? LIMIT 1", (rid,))
        rows = cur.fetchall()


        # conn = sqlInterface.dict_sql_connection()
        # cur = conn.cursor()
        # cur.execute("SELECT eid, title, owner, ptime, location, logo, description FROM event WHERE privacy<? ORDER BY eid DESC LIMIT ?", (6, limit))
        # rows = cur.fetchall()


        if len(rows) != 0:
            person['url'] = 'runner?rid='+str(rid)
            person['image'] = rows[0]['avatar']
            person['alt'] = rows[0]['username']
            person['title'] = rows[0]['username']

        conn.commit()
        conn.close()
        return person


    def get_runner_detail(rid, trid):
        runner_detail = {}
        runner_detail['basic_info'] = RunnerDAO.get_runner_basic_rid(trid)
        runner_detail['event_list'] = RunnerDAO.get_runner_event_list(rid, trid)
        runner_detail['group_list'] = RunnerDAO.get_runner_group_list(rid, trid)

        return runner_detail

    def set_event_role(rid, eid, role):
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO runner2event(rid, eid, role) VALUES(?, ?, ?)", (rid, eid, role,))
        # db.execute("INSERT INTO runner2event(rid, eid, role) VALUES (:rid, :eid, :role)", rid=rid, eid=eid, role=3)
        # rows = cur.fetchall()
        # print("test")
        conn.commit()
        conn.close()


    def set_group_role(rid, gid, role):
        conn = sqlInterface.create_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO runner2group(rid, gid, role) VALUES (?, ?, ?)", (rid, gid, role,))
        conn.commit()
        conn.close()



    def get_runner_event_list(rid, trid, limit=6, start=0):
        event_list = []
        event_id_list = EventDAO.get_eid_list_runner(trid)
        for id in event_id_list:
            event = EventDAO.get_event_basic_eid(id)
            event_list.append(event)

        return event_list


    def get_runner_group_list(rid, trid, limit=6, start=0):
        group_list = []
        group_id_list = GroupDAO.get_gid_list_runner(trid)
        for id in group_id_list:
            group = GroupDAO.get_group_basic_gid(id)
            group_list.append(group)

        return group_list


class Role:
    Visitor = 0     # visitor
    Invited = 1     # invited
    Pending = 2     # still waiting for Admin Aprove
    Member  = 3     # a member of event or group
    Admin   = 4     # administor of an event or a group, who can edit.
    Owner   = 5     # creator of an event or a group
    Ghost   = -1    #


def visit(url):
    redirect(url)

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    if session.get("runner_id") is None:
        runner_id = 0
        runner = {}
    else:
        runner_id = session['runner_id']
        runner = RunnerDAO.get_runner_basic_rid(runner_id)
    return render_template("apology.html", top=code, bottom=escape(message), runner=runner), code

# def main():
#     # database = r"C:\sqlite\db\pythonsqlite.db"

#     # create a database connection
#     # conn = create_connection('moonchaser.db')
#     group = {'url': 'event?eid=15', 'title': 'test_333', 'img': '/static/img/event/default_1.jpg', 'alt': 'test', 'description': 'asd', 'date': 'asd', 'time': 'asd', 'address': 'asds'}
#     ueid = EventDAO.update_event(3, event, 15)

#     print(ueid)


# if __name__ == '__main__':
#     main()

