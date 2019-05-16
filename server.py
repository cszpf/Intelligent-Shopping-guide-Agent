from flask import Flask
from flask import render_template
from flask import request, jsonify, send_file
from dialog_manager import DialogManager
import time

app = Flask(__name__)
manager = DialogManager()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dialog', methods=['GET', 'POST'])
def dialog():
    begin_time = time.time()
    token = request.args.get('token')
    domain = request.args.get('domain')
    sentence = request.args.get('message')
    if sentence is None:
        return jsonify({'error': 'bad request'})
    sentence = sentence.strip()
    sentence = sentence.lower()
    manager.user(domain, sentence, token)
    res = manager.response(token)
    print("本轮用时:", time.time() - begin_time)
    print(res)
    return jsonify(res)


@app.route('/resetDialog', methods=['GET', 'POST'])
def resetDialog():
    token = request.args.get('token')
    print("reset:", token)
    manager.reset(token)
    return "reset done!"


@app.route('/error_dialog', methods=['GET', 'POST'])
def error_dialog():
    token = request.args.get('token')
    print("mark error:", token)
    manager.mark_error(token)
    return "mark done!"


@app.route('/intent_classifier/<filename>', methods=['GET'])
def intent_classifier(filename):
    return send_file('./static/models/' + filename)


if __name__ == '__main__':
    manager.user('computer', '我想买电脑', 'init')
    manager.reset('init')
    manager.user('phone', '我想买手机', 'init')
    manager.reset('init')
    manager.user('camera', '我想买相机', 'init')
    manager.reset('init')
    manager.record_history = True
    app.run('0.0.0.0', port='5000')
