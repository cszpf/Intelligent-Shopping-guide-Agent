from flask import Flask
from flask import render_template
from flask import request, jsonify, send_file
from dialog_manager import DialogManager

app = Flask(__name__)
manager = DialogManager()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dialog', methods=['GET', 'POST'])
def dialog():
    domain = request.args.get('domain')
    sentence = request.args.get('message')
    sentence = sentence.strip()
    manager.user(domain, sentence)
    res = manager.response()
    return jsonify(res)


@app.route('/resetDialog', methods=['GET', 'POST'])
def resetDialog():
    manager.reset()
    return "reset done!"

@app.route('/intent_classifier/<filename>',methods=['GET'])
def intent_classifier(filename):
    return send_file('./static/models/'+filename)


if __name__ == '__main__':
    app.run('127.0.0.1', port='5000')
