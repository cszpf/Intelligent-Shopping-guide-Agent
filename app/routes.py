from app import app as bot_app
from uuid import uuid4
from flask import render_template, request, jsonify, session
from app.backend.dialogue import Dialogue

dialog = Dialogue()


@bot_app.route('/')
@bot_app.route('/index', methods=['GET', 'POST'])
def index():
    #form = ChatForm(request.form)
    # print(session['sid'])
    if 'sid' not in session.keys() :    
        session['sid'] = uuid4()       
    # if form.is_submitted():
        # return Response('text')
    return render_template('index.html')


@bot_app.route('/message', methods=['GET', 'POST'])
def message():
    msg = request.form['message']
    bot_response = dialog.Dialogue_manager(msg)
    return jsonify({'text': bot_response})
