from . import app
from flask import Flask, request, render_template
import re
import database_helper
import random
import json
from geventwebsocket import WebSocketError
from flask.ext.bcrypt import Bcrypt
import hashlib
import time

#app = Flask(__name__)
bcrypt = Bcrypt(app)
sockets = dict()


@app.before_request
def before_request():
    database_helper.connect_db()


@app.teardown_request
def teardown_request(exception):
    database_helper.close_db()


@app.route('/')
def start():
    return render_template('client.html')


@app.route('/socketconnect')
def connect_socket():
    #print "- SOMEONE JUST TRIED TO CONNECT

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        rcv = ws.receive()
        data = json.loads(rcv)
        #Info received from the client
        email = data['email']
        hashed_data = data['hashedData']
        timestamp = data['timestamp']

        if check_tok('socketconnect',email,hashed_data,str(int(timestamp)),False):
            if not database_helper.get_logged_in(database_helper.get_token_by_mail(email)[0]):
                ws.send(json.dumps({"success": False, "message": "Token not in the database !"}))

            try:
                #If the user's email is in the sockets dict already
                if email in sockets:
                    print str(email) + " has an active socket already"

                #We save the active websocket for the logged in user
                print "Saving the socket for the user : " + str(email)
                sockets[str(email)] = ws
                #print(sockets)

                # We listen on the socket and keep it active
                while True:
                    rcv = ws.receive()
                    if rcv == None:
                        del sockets[str(email)]
                        ws.close()
                        print "Socket closed for the user : " + str(email)
                        return ""

            except WebSocketError as err:
                repr(err)
                print("WebSocketError !")
                del sockets[str(email)]

        return ""
    return json.dumps({"success": False, "message": "Error request."})



# Checks if hash from client = hash from server
def check_tok(path,email,hashed_data,timestamp,post):
    data = database_helper.get_logged_in_by_mail(email)
    if data == None:
        return json.dumps({"success": False, "message": "You are not logged in."})

    slack = 300 #5min
    t1 = int(time.time() + slack)
    t2 = int(time.time() - slack)

    if (int(timestamp) < t1 and int(timestamp) > t2):
        token = data[0]
        if post:
            data_to_hash = '/'+path+"&email="+email+"&token="+token+"&timestamp="+timestamp
        else:
            data_to_hash = '/'+path+'/'+email+'/'+token+"/"+timestamp

        #Encoding data to hash (string) to bytes
        hash = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

        print("dataToHash: "+data_to_hash)
        print("hash from client: "+hash)
        print("hash from server: "+str(hashed_data))
        print ("timestamp " + str(timestamp))
        print ("t1 " + str(t1))
        print ("t2 " + str(t2))

        #True if the user is legitimate
        return (hashed_data == hash)
    return "Time exceeded"

#Generates the route for post requests and then checks if hash from client = hash from server
def	check_tok_post(path, request):
    path += "?"
    email = ""
    timestamp = ""
    hashed_data = ""
    for key in request.form:
        if key == "hashedData":
            hashed_data = request.form[key]
        elif key == "email":
            email = request.form[key]
        elif key == "timestamp":
            timestamp = request.form[key]
        else:
            path += key+"="+request.form[key]+"&"

    path = path[:-1]
    print("path : "+path)
    return check_tok(path, email, hashed_data, str(int(timestamp)), True)

@app.route('/signup', methods=['POST'])
def sign_up():
    # if request.method == 'POST':
    email = request.form['emailSign']
    password = request.form['passwordSign']
    firstname = request.form['firstName']
    familyname = request.form['familyName']
    gender = request.form['gender']
    city = request.form['city']
    country = request.form['country']

    if (check_email(email) == True) and len(password) >= 6 \
            and (check_gender(gender)) \
            and len(firstname) > 0 and len(familyname) > 0 \
            and len(city) > 0 and len(country) > 0:
        hashedPwd = bcrypt.generate_password_hash(password)
        signUp = database_helper.insert_user(email, hashedPwd, firstname, familyname, gender, city, country)
        if signUp:
            return json.dumps({"success": True, "message": "Successfully created a new user."})
        else:
            return json.dumps({"success": False, "message": "Form data missing or incorrect type."})
    else:
        return json.dumps({"success": False, "message": "Form data missing or incorrect type."})


# Authenticates the username by the provided password
@app.route('/signin', methods=['POST'])
def sign_in():
    #print "SOMEONE JUST SIGNED IN"
    email = request.form['emailLog']
    password = request.form['passwordLog']
    data_user = database_helper.get_user(email)

    if data_user == None:
        return json.dumps({'success': False, 'message': "User doesn't exist."})

    if bcrypt.check_password_hash(data_user[1],password):
        token = create_token()

        if database_helper.get_logged_in_by_mail(email):
            if email in sockets:
                # Removing the other token if the user signs in again
                try:
                    ws = sockets[str(email)]
                    ws.send(json.dumps({'success': False, 'message': "You've been logged out !"}))
                except WebSocketError as err:
                    repr(err)
                    print("WebSocketError !")
                    #The socket is closed already
                    del sockets[str(email)]
                except Exception, err:
                    print err
            database_helper.remove_logged_in_by_mail(email)

        database_helper.add_logged_in(token, email)
        return json.dumps({'success': True, 'message': "Login successful!", 'token': token, 'email': email})

    else:
        return json.dumps({'success': False, 'message': "User doesn't exist."})

# Creates a random token
def create_token():
    ab = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    token = ''
    for i in range(0, 36):
        token += ab[random.randint(0, len(ab) - 1)]
    return token


# Checks if an email address is valid
def check_email(email):
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return True
    return False


#Checks if the gender is valid
def check_gender(gender):
    return gender == 'male' or gender == 'female'


# Signs out a user from the system
@app.route('/signout', methods=['POST'])
def sign_out():
    token = request.form['token']
    if database_helper.get_logged_in(token):
        database_helper.remove_logged_in(token)
        return json.dumps({"success": True, "message": "Successfully signed out."})
    else:
        return json.dumps({"success": False, "message": "You are not signed in"})


# Changes the password from the current user to a new one
@app.route('/changepassword', methods=['POST'])
def change_password():
    email = request.form['email']
    pwd = request.form['pwd']
    chgpwd = request.form['chgPwd']
    timestamp = request.form['timestamp']
    #Secure way to transmission of data
    if check_tok_post('changepassword', request):
        if not database_helper.get_logged_in_by_mail(email):
            return json.dumps({'success': False, 'message': "You are not logged in."})

        else:
            if len(chgpwd) < 6:
                return json.dumps({"success": False, "message": "Error: password must be at least 6 characters long"})

            current_password = database_helper.get_user(email)[1]

            if bcrypt.check_password_hash(current_password, pwd):
                database_helper.modify_pwd(email, current_password, bcrypt.generate_password_hash(chgpwd))
                return json.dumps({"success": True, "message": "Password changed."})
            return json.dumps({"success": False, "message": "Error : invalid inputs."})
    return json.dumps({"success": False, "message": "Error request."})

# Retrieves the stored data for the user whom the passed token is issued for.
# The currently signed-in user case use this method to retrieve all its own info from the server
@app.route('/getuserdatabytoken/<mailUser>/<timestamp>/<hashedData>', methods=['GET'])
def get_user_data_by_token(mailUser,timestamp,hashedData):
    if database_helper.get_logged_in_by_mail(mailUser):
        data = database_helper.get_user_data_by_email(mailUser)
        if check_tok('getuserdatabytoken',mailUser,hashedData,str(int(timestamp)),False):
            if data is not None:
                return json.dumps({"success": True, "message": "User data retrieved.", "data": data})
            return json.dumps({"success": False, "message": "No such user."})
        return json.dumps({"success": False, "message": "No such user."})
    return json.dumps({"success": False, "message": "You are not signed in."})


# Retrieves the stored data for the user specified by the email address
@app.route('/getuserdatabyemail/<mailUser>/<email>/<timestamp>/<hashedData>', methods=['GET'])
def get_user_data_by_email(email, mailUser, timestamp, hashedData):
    if database_helper.get_logged_in_by_mail(mailUser):
        data = database_helper.get_user_data_by_email(email)
        if check_tok('getuserdatabyemail/'+mailUser,email,hashedData,str(int(timestamp)),False):
            if data is not None:
                return json.dumps({"success": True, "message": "User data retrieved.", "data": data})
            return json.dumps({"success": False, "message": "User data not retrieved.", "data": data})
        return json.dumps({"success": False, "message": "No such user."})
    else:
        return json.dumps({"success": False, "message": "You are not signed in."})


# Tries to post a message to the wall of the user specified by the email address
@app.route('/postmessage', methods=['POST'])
def post_message():
    message = request.form['message']
    email = request.form['mail']
    mailUser = request.form['mailUser']
    timestamp = request.form['timestamp']
    sender = mailUser
    if database_helper.get_logged_in_by_mail(mailUser):
        if database_helper.in_users(email):
            #Secure way to transmission of data
            if check_tok_post("postmessage",request):
                token = database_helper.get_token_by_mail(sender)[0]
                database_helper.post_message(message, token, sender, email)
                return json.dumps({"success": True, "message": "Message posted."})
        else:
            return json.dumps({"success": False, "message": "Message not posted."})
    else:
        return json.dumps({"success": False, "message": "You are not signed in."})


# Retrieves the stored messages for the user whom the passed token is issued for.
# The currently signed-in user case use this method to retrieve all its own messages from the server.
@app.route('/getusermessagesbytoken/<mailUser>/<timestamp>/<hashedData>', methods=['GET'])
def get_user_messages_by_token(mailUser,hashedData,timestamp):
    if database_helper.get_logged_in_by_mail(mailUser):
        if check_tok('getusermessagesbytoken',mailUser,hashedData,str(int(timestamp)),False):
            token = database_helper.get_token_by_mail(mailUser)[0]
            data = database_helper.get_user_messages_by_token_db(token)
            if data is not None:
                return json.dumps({"success": True, "message": "User messages retrieved.", "data": data})
        return json.dumps({"success": False, "message": "No such user."})
    return json.dumps({"success": False, "message": "You are not signed in."})


# Retrieves the stored messages for the user specified by the passed email address
@app.route('/getusermessagesbyemail/<mailUser>/<email>/<timestamp>/<hashedData>', methods=['GET'])
def get_user_messages_by_email(email,mailUser, timestamp, hashedData):
    if database_helper.get_logged_in_by_mail(mailUser):
        if (database_helper.in_users(email)):
            if check_tok('getusermessagesbyemail/'+mailUser,email,hashedData,str(int(timestamp)),False):
                data = database_helper.get_user_messages_by_email_db(email)
                return json.dumps({"success": True, "message": "User messages retrieved.", "data": data})
        return json.dumps({"success": False, "message": "No such user."})
    else:
        return json.dumps({"success": False, "message": "You are not signed in."})