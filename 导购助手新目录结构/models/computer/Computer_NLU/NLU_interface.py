import tensorflow as tf
import pickle
import sys
import os
sys.path.append(os.path.dirname(__file__))
from model import Model

from utils import get_logger, create_model
from utils import load_config
from data_utils import load_word2vec, input_from_line

from create_data import get_tags_single_text
##########################
# 预先设定好的参数
flags = tf.app.flags
flags.DEFINE_string("ckpt_path",    "ckpt",      "Path to save model")
flags.DEFINE_string("log_file",     "train.log",    "File for log")
flags.DEFINE_string("map_file",     "maps.pkl",     "file for maps")
flags.DEFINE_string("config_file",  "config_file",  "File for config")
FLAGS = tf.app.flags.FLAGS

# 全局启动tensoflw
def get_slot_dl(text):
    """
    获得一个句子的slot_table
    :param text: 用户输入的句子
    # :param tf_sess: tensorflow 的sessiong
    :return:
    """
    tf.reset_default_graph()   # FIXME: 为了可以保证重复多次输入(不过会很慢)整合代码时，可以尝试将NLU和DM分离，使用统一的文件管理。
    FLAGS.config_file = '/forum_config/config_file'
    FLAGS.log_file = '/forum_config/log/train.log'
    FLAGS.ckpt_path = '/forum_ckpt/'
    FLAGS.map_file = '/forum_config/maps.pkl'
    
    file_path = os.path.dirname(__file__)
    config = load_config(file_path+FLAGS.config_file)
    logger = get_logger(file_path+FLAGS.log_file)
    # limit GPU memory
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    with open(file_path+FLAGS.map_file, "rb") as f:
        char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)
    with tf.Session(config=tf_config) as sess:
        model = create_model(sess, Model, FLAGS.ckpt_path, load_word2vec, config, id_to_char, logger)
        result = model.evaluate_line(sess, input_from_line(text, char_to_id), id_to_tag)
    return result

def get_slot_re(text):
    """
    使用规则来识别slot
    :param text:
    :return:
    """
    tag_init = ['O']*len(text)
    tag_list = get_tags_single_text({'text': text, 'tag': tag_init})
    assert len(tag_init) == len(text)
    i = 0
    result = {}
    result['string'] = text
    result['entities'] = list()
    while i < len(tag_list) :
        tag = tag_list[i]
        # print(tag)
        if 'B-' in tag:  # 找到一个标签
            start_index = i
            tag_type = tag.split('-')[1]  # 拿去类型
            end_index = i + 1
            while end_index < len(tag_list) and tag_list[end_index] != 'O' :  # 直到标签结束
                end_index += 1
            word = text[start_index:end_index]
            word = word.strip()
            i = end_index
            result['entities'].append({'word':word, 'start':start_index, 'end':end_index, 'type':tag_type})
        else:
            i += 1
    return result


def get_slot_table(text):
    """
    NLU提供给对话关系模块的数据
    :param text:
    :return:
    """
    slot_table = {}
    tag_dl = get_slot_dl(text)
    # print('dl', tag_dl)
    tag_re = get_slot_re(text)
    # print('re', tag_re)

    for entity in tag_dl['entities']:
        slot_table[entity['type'].lower()] = entity['word']
    for entity in tag_re['entities']:
        if entity['type'].lower() in slot_table and 'price' in entity['type']:   # 表示在dl中已经识别出来了
            continue
        else:
            slot_table[entity['type'].lower()] = entity['word']
    return slot_table



