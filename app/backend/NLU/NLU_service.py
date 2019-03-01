#!flask/bin/python
import pickle
import re

import jieba
from flask import Flask
import tensorflow as tf

from Slot_part.model import Model
from Slot_part.utils import get_logger, create_model
from Slot_part.utils import load_config
from Slot_part.data_utils import load_word2vec, input_from_line, clean_line, line_to_id
from Slot_part.utils import result_to_json_iob

import CONFIG

app = Flask(__name__)

def clean(text):
    text = re.sub(r' ', '', text)
    text = re.sub(r'[’!"#$%&\'()*+,-/:;<=>@,。★、…【】《》“”‘’！^_`{|}~]+', '', text)
    clean_words = []
    for word in jieba.cut(text):
        clean_words.append(word)
    return ' '.join(clean_words)

def transform_digital(text):
    sequence = re.sub(r'\d', 'x', text)
    sequence = re.sub(r'[一二三四五六七八九十零百千]', 'x', sequence)
    sequence = re.sub(r'x[.]x', 'xxx', sequence)
    sequence = sequence.lower()
    return sequence

intend_model_path = CONFIG.NLU_path + '\\Intend_part\\model\\model.pk'
with open(intend_model_path, 'rb') as fr:
    save = pickle.load(fr)
    intend_tfidf_model = save['tfidfVectorizer']
    intend_classifier_model = save['classifier_model']
    intend_label_subject = save['label_subject']

requirement_model_path = CONFIG.NLU_path + '\\Requirement_part\\model\\model.pk'
with open(requirement_model_path, 'rb') as fr:
    save = pickle.load(fr)
    requirement_tfidf_model = save['tfidfVectorizer']
    requirement_classifier_model = save['classifier_model']
    requirement_label_subject = save['label_subject']


FLAGS_camera = tf.app.flags.FLAGS
tf.reset_default_graph()
FLAGS_camera.config_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\config_file'
FLAGS_camera.log_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\log\\train.log'
FLAGS_camera.ckpt_path = CONFIG.NLU_path + '\\Slot_part\\forum_ckpt'
FLAGS_camera.map_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\maps.pkl'

config_camera = load_config(FLAGS_camera.config_file)
config_camera['emb_file'] = CONFIG.NLU_path + '\\Slot_part\\' + config_camera['emb_file']
logger_camera = get_logger(FLAGS_camera.log_file)
# limit GPU memory
tf_config_camera = tf.ConfigProto()
tf_config_camera.gpu_options.allow_growth = True

with open(FLAGS_camera.map_file, "rb") as f:
    char_to_id_camera, id_to_char_camera, tag_to_id_camera, id_to_tag_camera = pickle.load(f)
sess_camera = tf.Session(config=tf_config_camera)
model_camera = create_model(sess_camera, Model, FLAGS_camera.ckpt_path, load_word2vec, config_camera, id_to_char_camera, logger_camera)

FLAGS_phone = tf.app.flags.FLAGS
tf.reset_default_graph()
FLAGS_phone.config_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\phone_config_file'
FLAGS_phone.log_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\log\\phone_train.log'
FLAGS_phone.ckpt_path = CONFIG.NLU_path + '\\Slot_part\\forum_ckpt\\phone'
FLAGS_phone.map_file = CONFIG.NLU_path + '\\Slot_part\\forum_config\\phone_maps.pkl'

config_phone = load_config(FLAGS_phone.config_file)
config_phone['emb_file'] = CONFIG.NLU_path + '\\Slot_part\\' + config_phone['emb_file']
logger_phone = get_logger(FLAGS_phone.log_file)
# limit GPU memory
tf_config_phone = tf.ConfigProto()
tf_config_phone.gpu_options.allow_growth = True

with open(FLAGS_phone.map_file, "rb") as f:
    char_to_id_phone, id_to_char_phone, tag_to_id_phone, id_to_tag_phone = pickle.load(f)

sess_phone = tf.Session(config=tf_config_phone)
model_phone = create_model(sess_phone, Model, FLAGS_phone.ckpt_path, load_word2vec, config_phone, id_to_char_phone, logger_phone)

"""
camera slot识别接口
"""
@app.route('/NLU/get_slot_camera/<string:sentence>', methods=['GET'])
def get_slot_camera(sentence):
    with sess_camera.as_default():
        sentence = clean_line(sentence)
        changed_sequence = transform_digital(sentence)
        inputs, tags = model_camera.evaluate_line_no_json(sess_camera, input_from_line(changed_sequence, char_to_id_camera), id_to_tag_camera)
        result = result_to_json_iob(sentence, tags)
        return str(result)

"""
phone slot识别接口
"""
@app.route('/NLU/get_slot_phone/<string:sentence>', methods=['GET'])
def get_slot_phone(sentence):
    with sess_phone.as_default():
        sentence = clean_line(sentence)
        changed_sequence = transform_digital(sentence)
        # result = model_phone.evaluate_line(sess_phone, input_from_line(sentence, char_to_id_phone), id_to_tag_phone)
        inputs, tags = model_phone.evaluate_line_no_json(sess_phone, line_to_id(changed_sequence, char_to_id_phone), id_to_tag_phone)
        result = result_to_json_iob(sentence, tags)
        return str(result)

"""
intend 识别接口
"""
@app.route('/NLU/get_intend/<string:sentence>', methods=['GET'])
def get_intend(sentence):
    sentence = clean(sentence)
    sentence_list = [sentence]
    sentence_term_doc = intend_tfidf_model.transform(sentence_list)
    label = intend_classifier_model.predict(sentence_term_doc)
    return intend_label_subject[label[0]]

"""
需求识别接口
"""
@app.route('/NLU/get_requirement/<string:sentence>', methods=['GET'])
def get_requirement(sentence):
    sentence = clean(sentence)
    sentence_list = [sentence]
    sentence_term_doc = requirement_tfidf_model.transform(sentence_list)
    label = requirement_classifier_model.predict(sentence_term_doc)
    return requirement_label_subject[label[0]]

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9999)