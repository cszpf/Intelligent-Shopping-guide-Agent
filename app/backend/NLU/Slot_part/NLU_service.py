#!flask/bin/python
import pickle
import re
import tensorflow as tf
import pickle

import time

from model import Model

from utils import get_logger, create_model
from utils import load_config
from data_utils import load_word2vec, input_from_line

import jieba
from flask import Flask

app = Flask(__name__)

FLAGS = tf.app.flags.FLAGS
tf.reset_default_graph()   # FIXME: 为了可以保证重复多次输入(不过会很慢)整合代码时，可以尝试将NLU和DM分离，使用统一的文件管理。
FLAGS.config_file = 'D:\\pythonWorkPrpject\\Intelligent-Shopping-guide\\NLU\Slot_part\\forum_config\\config_file'
FLAGS.log_file = 'D:\\pythonWorkPrpject\\Intelligent-Shopping-guide\\NLU\\Slot_part\\forum_config\\log\\train.log'
FLAGS.ckpt_path = 'D:\\pythonWorkPrpject\\Intelligent-Shopping-guide\\NLU\\Slot_part\\forum_ckpt'
FLAGS.map_file = 'D:\\pythonWorkPrpject\\Intelligent-Shopping-guide\\NLU\\Slot_part\\forum_config\\maps.pkl'

config = load_config(FLAGS.config_file)
logger = get_logger(FLAGS.log_file)
# limit GPU memory
tf_config = tf.ConfigProto()
tf_config.gpu_options.allow_growth = True

@app.route('/NLU/get_slot/<string:sentence>', methods=['GET'])
def get_requirement(text):
    with open(FLAGS.map_file, "rb") as f:
        char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)
    with tf.Session(config=tf_config) as sess:
        model = create_model(sess, Model, FLAGS.ckpt_path, load_word2vec, config, id_to_char, logger)
        result = model.evaluate_line(sess, input_from_line(text, char_to_id), id_to_tag)
    return result

if __name__ == '__main__':
    app.run(debug=True)