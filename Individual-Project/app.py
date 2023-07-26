from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
import pyrebase
import base64
import math
import uuid
config = {
  'apiKey': "AIzaSyBYar8IhOYZWw0mPemkqNl4NMsP1vWgwD8",

  'authDomain': "final1-fe83a.firebaseapp.com",

  'projectId': "final1-fe83a",

  'storageBucket': "final1-fe83a.appspot.com",

  'messagingSenderId': "290232941428",

  'appId': "1:290232941428:web:0bbcfade217234b55b4a21",

  "databaseURL":'https://final1-fe83a-default-rtdb.europe-west1.firebasedatabase.app/'
}

firebase=pyrebase.initialize_app(config)
db=firebase.database()
# temp=[1]
# db.child('UID_list').child('list').set(temp)
# print(db.child('UID_list').child('list').get().val())
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'super-secret-key'
auth= firebase.auth()


@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method=="POST":
        user=request.form["email"]
        password= request.form["password"]
        try:
            login_session['user']=auth.sign_in_with_email_and_password(user, password)
            return (redirect(url_for('home')))
        except Exception as e:
            error=e
            print(f"ERROR: {e}")
    return render_template("signin.html")

@app.route('/profile_edit', methods=['GET', 'POST'])
def profile_edit():
    if request.method== 'POST':
        UID=login_session['user']['localId']
        file = request.files['profile_pic']
        phone=request.form['phone']
        if file.filename == '':
            return "No selected file", 400
        image_data = file.read()
        base64_encoded = base64.b64encode(image_data).decode('utf-8')
        name=request.form['name']
        bio=request.form['bio']
        gender=request.form['gender']
        attraction=request.form['attraction']
        user={'name':name, 'bio':bio, 'gender' :gender,'attraction':attraction, 'picture':base64_encoded, 'matchindex':0, 'rating':1200, 'UID':UID, 'matches':[0], 'phone':phone, 'notifications':['']}
        db.child('users').child(UID).update(user)
        user=db.child('users').child(UID).get().val()
        return redirect(url_for('home'))
    return render_template('profile_edit.html')
@app.route('/message')
def message():
    UID=login_session['user']['localId']
    index=db.child('users').child(UID).child('matchindex').get().val()
    match_UID=db.child('UID_list').child('list').get().val()[index]
    match= db.child('users').child(match_UID).get().val()
    return render_template('message.html', match= match)
@app.route('/home', methods=['GET', 'POST'])
def home():
    try:
        UID=login_session['user']['localId']
        rating2= db.child('users').child(UID).child('rating').get().val()
        if request.method=='POST':
            index=db.child('users').child(UID).child('matchindex').get().val()
            match_UID=db.child('UID_list').child('list').get().val()[index]
            match= db.child('users').child(match_UID).get().val()
            rating1=match['rating']
            if request.form['swipe']=='Yes':
                score=1
            else:
                score=0
            p_win = (1.0 / (1.0 + math.pow(10, ((rating2 - rating1) / 400)))); 
            rating1=rating1+50*(score-p_win)
            db.child('users').child(match_UID).update({'rating':rating1})
            if match_UID in db.child('users').child(UID).child('matches').get().val():
                db.child('users').child('match_UID').child('notifications').push("congradulations!, you have matched with "+ match['name']+ " , u can contact them using their mobile phone (couldnt get the messaging working)- "+ match['phone'])
                return redirect(url_for('message'))

            else:
                temp=db.child('users').child (match_UID).child('matches').get().val()
                temp.append(UID)
                db.child('users').child(match_UID).update({'matches':temp})


                         
        else:
            index=db.child('users').child(UID).child('matchindex').get().val()
        index+=1
        match_UID=db.child('UID_list').child('list').get().val()[index]
        match= db.child('users').child(match_UID).get().val()
        rating1=match['rating']
        db.child('users').child(UID).update({'matchindex':index})
        match_UID=db.child('UID_list').child('list').get().val()[index]
        match= db.child('users').child(match_UID).get().val()  
        rating1=match['rating'] 
        if match['gender']==db.child('users').child('UID').child('attraction').get().val() and match[attraction]== db.child('users').child('UID').child('gender').get().val():
            if match[name]==db.child('users').child('UID').child('name').get().val(): #so you wont date urself
                return redirect(url_for('home'))
        if math.isclose(rating1, rating2,rel_tol =100):
            return render_template('home.html', match= match )
        else:
            return redirect(url_for('home'))

    except Exception as e:
        print(f"ERROR: {e}")
        return "i dont know how but we ran out of people on this site for you- if you want to continue i suggest talking to people irl"
@app.route('/notifications')
def notifications():
    UID=login_session['user']['localId']
    notifications=db.child('users').child(UID).child('notifications').get().val()
    return render_template("notifications.html", notifications= notifications)
@app.route('/view_chats')
def view_chats():
    UID= login_session['user']['localId']
    chats=db.child('users').child(UID).child('chats').get().val()
    chat_list=[]
    name= db.child('users').child(UID).child('name').get().val()
    for chat in chats:
        chat_list.append(db.child('chats').child(chat).get().val())
    return render_template('chats.html' , chats=chat_list, name=name)

@app.route('/newchat')
def newchat():
    UID= login_session['user']['localId']
    index=db.child('users').child(UID).child('matchindex').get().val()
    match_UID=db.child('UID_list').child('list').get().val()[index]
    chatUID= uuid.uuid4()
    chatUID=str(chatUID)
    match=db.child('users').child(match_UID).get().val()
    db.child('chats').update({chatUID:[db.child('users').child(UID).child('name').get().val(), match['name'], chatUID]})
    db.child('users').child(UID).child('chats').push(chatUID)
    db.child('users').child(match_UID).child('chats').push(chatUID)
    return redirect(url_for('/chat/'+ chatUID))
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method=="POST":
        user=request.form["email"]
        password= request.form["password"]
        try:
            login_session['user']=auth.create_user_with_email_and_password(user, password)
            user= {'email': user, }
            UID= login_session['user']['localId']
            UID_list=db.child('UID_list').child('list').get().val()
            UID_list.append(UID)
            db.child("UID_list").update({'list':UID_list})
            db.child('users').child(UID).set(user)
            return redirect(url_for('profile_edit'))
        except Exception as e:
            error='authentication error'
            print(f"ERROR: {e}")
    return render_template("signup.html")

@app.route('/chat/<string:chatUID>', methods=['GET', 'POST'])
def chat():
    UID=login_session['user']['localId']
    name= db.child('users').child('UID').child('name').get().val()
    chat= db.child('chats').child(chatUID).get().val()
    if request.method=='POST':
        response= request.form('response')
        response={'message':response, 'author':name}
        chat.append(response)
        db.child('chats').update({chatUID:chat})
    if chat[0]==name:
        responder=chat[1]
    else:
        responder=chat[0]
    return render_template('view_chat.html', chat=chat, name=name, responder=responder)
@app.route("/signout")
def signout():
    auth.current_user=None
    login_session['user']=None
    return (redirect(url_for('signin')))


if __name__ == '__main__':
    app.run(debug=True)