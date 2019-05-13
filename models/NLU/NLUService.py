from __future__ import print_function
import nltk
import pickle
import sys
import os
import tensorflow as tf

global graph
graph = tf.get_default_graph()

sys.path.append(os.path.dirname(__file__))
from path_config import Config
from slot_part.util.preprocessing import create_matrices
from slot_part.util.preprocessing import transform_digital
from slot_part.util.preprocessing import clean as slot_clean
from slot_part.util.BIOF1Validation import result_to_json_iob
from slot_part.networks.BiLSTM import BiLSTM
from intention_part.main import clean as intention_clean
from intention_part.main import load_aspect_sentiment
from requirement_part.main import clean as requirement_clean


def split_all(s, target=',.?，。？！!'):
    '''
    split a sentence by target
    :param s: input sentence
    :param target: target string
    :return:a list of string
    '''
    sent = []
    line = ''
    for word in s:
        if word not in target:
            line += word
        else:
            sent.append(line)
            line = ''
    if line != '':
        sent.append(line)
    return sent


class NLUService(object):
    """
    NLU Service:
    include 1. slot filling service for phone, computer, camera
            2. intention recognition service
            3. requirement recognition service
    """

    def __init__(self, ):
        self.intention_recognition_model = None
        self.requirement_recognition_model = None
        self.computer_slot_model = None
        self.phone_slot_model = None
        self.camera_slot_model = None

        self.config = Config()

        # :: all model path ::
        self.computer_model_path = self.config.SLU_path + '/slot_part/models/computer_0.9367_0.9451_40.h5'
        self.phone_model_path = self.config.SLU_path + '/slot_part/models/phone_0.9464_0.9319_34.h5'
        self.camera_model_path = self.config.SLU_path + '/slot_part/models/camera_0.9846_0.9751_30.h5'
        self.intention_model_path = self.config.SLU_path + '/intention_part/model/model.pk'
        self.requirement_model_path = self.config.SLU_path + '/requirement_part/model/model.pk'

        # :: Load the slot model ::
        self.computer_slot_model = BiLSTM.load_model(self.computer_model_path)
        self.phone_slot_model = BiLSTM.load_model(self.phone_model_path)
        self.camera_slot_model = BiLSTM.load_model(self.camera_model_path)

        # :: Load the intention model ::
        with open(self.intention_model_path, 'rb') as fr:
            save = pickle.load(fr)
            self.intention_tfidf_model = save['tfidfVectorizer']
            self.intention_classifier_model = save['classifier_model']
            self.intention_label_subject = save['label_subject']

        # :: Load the intention model ::
        with open(self.requirement_model_path, 'rb') as fr:
            save = pickle.load(fr)
            self.requirement_tfidf_model = save['tfidfVectorizer']
            self.requirement_classifier_model = save['classifier_model']
            self.requirement_label_subject = save['label_subject']

        self.aspect_sentiment = load_aspect_sentiment()

    def computer_slot_predict(self, sentence):
        """
        get the slot value of sentences about computer.

        :param sentence:
        :return: the json result of the slot value like {brand: ['华为'], price: ['2000']}
        """

        sentence = slot_clean(sentence)
        text = ' '.join([word for word in sentence])

        # :: Prepare the input ::
        sentences = [{'tokens': nltk.word_tokenize(text)}]
        data_matrix = create_matrices(sentences, self.computer_slot_model.mappings, True)

        # :: Tag the input ::
        with graph.as_default():
            tags = self.computer_slot_model.tag_sentences(data_matrix)

        return result_to_json_iob(sentence, tags['computer'][0])  # fixme:  'computer' should be a var

    def phone_slot_predict(self, sentence):
        """
        get the slot value of sentences about phone.

        :param sentence:
        :return: the json result of the slot value like {brand: ['华为'], price: ['2000']}
        """

        sentence = slot_clean(sentence)
        text = ' '.join([word for word in sentence])

        # :: Prepare the input ::
        sentences = [{'tokens': nltk.word_tokenize(text)}]
        data_matrix = create_matrices(sentences, self.phone_slot_model.mappings, True)

        # :: Tag the input ::
        with graph.as_default():
            tags = self.phone_slot_model.tag_sentences(data_matrix)

        return result_to_json_iob(sentence, tags['phone'][0])  # fixme:  'phone' should be a var

    def camera_slot_predict(self, sentence):
        """
        get the slot value of sentences about phone.

        :param sentence:
        :return: the json result of the slot value like {brand: ['佳能'], price: ['2000']}
        """

        # :: fixme: this is different from the other two because camera's dataset is different
        sentence = slot_clean(sentence)
        sentence_change_digital = transform_digital(sentence)
        # text = ' '.join([word for word in sentence_change_digital])
        text = ' '.join([word for word in sentence])

        # :: Prepare the input ::
        sentences = [{'tokens': nltk.word_tokenize(text)}]
        data_matrix = create_matrices(sentences, self.camera_slot_model.mappings, True)

        # :: Tag the input ::
        with graph.as_default():
            tags = self.camera_slot_model.tag_sentences(data_matrix)

        return result_to_json_iob(sentence, tags['camera'][0])  # fixme:  'camera' should be a var

    def intention_predict(self, sentence):
        """
        Get the intention label of the input sentence
        label_1: answer_no
        label_2: answer_yes
        label_3: answer_slot
        label_4: ask_slot_list

        :param sentence:
        :return: the label of the sentence like answer_no for the sentence "不是的".
        """

        sentence = intention_clean(sentence)
        sentence_list = [sentence]
        sentence_term_doc = self.intention_tfidf_model.transform(sentence_list)
        label = self.intention_classifier_model.predict(sentence_term_doc)
        return self.intention_label_subject[label[0]]

    def requirement_predict(self, sentence):
        """
        get the requirement label of the input sentence
        label_1: need
        label_2: no_need
        label_3: whatever

        :param sentence:
        :return: the label of the sentence like ( no_need ) for the sentence "我不要华为的".
        """
        sentence = requirement_clean(sentence)
        sentence_list = [sentence]
        sentence_term_doc = self.requirement_tfidf_model.transform(sentence_list)
        label = self.requirement_classifier_model.predict(sentence_term_doc)
        return self.requirement_label_subject[label[0]]

    def confirm_slot(self, slot_list, sentence, mode=3):
        '''
        :param slot_list: slot list to be confirmed
        :param sentence: user input
        :param mode: 1. aspect-based sentiment 2. intention based 3. rule based
        :return: slot_list with need attr
        '''
        print("confirm slot")
        print(slot_list)
        print(sentence)
        if mode == 1:
            for item in slot_list:
                slot = item['word']
                sentence = split_all(sentence, ',.?，。？！!')
                for sent in sentence:
                    if slot not in sent:
                        continue
                    sentiment = self.aspect_sentiment['predict'](sent, slot)
                    if sentiment == 'positive':
                        item['need'] = True
                    else:
                        item['need'] = False
            return slot_list
        elif mode == 2:
            intent = self.requirement_predict(sentence)
            if intent == 'need':
                for item in slot_list:
                    item['need'] = True
                return slot_list
            if intent == 'no_need':
                for item in slot_list:
                    item['need'] = False
                return slot_list
            if intent == 'whatever':
                for item in slot_list:
                    item['need'] = False
                return slot_list
        else:
            intent = self.requirement_predict(sentence)
            no_word = ['不要', '不是', '否定', '否认', '不对', '不可以', '不行', '别', '否', '不', '差']
            for item in slot_list:
                if item['type'] not in ['function', 'experience']:
                    if intent == 'need':
                        item['need'] = True
                    if intent == 'no_need':
                        item['need'] = False
                    if intent == 'whatever':
                        item['need'] = True
                    continue

                slot = item['word']
                sentence = split_all(sentence, ',.?，。？！!')
                for sent in sentence:
                    if slot not in sent:
                        continue
                    negative = False
                    for word in no_word:
                        if word in sent:
                            negative = True
                            break
                    if negative:
                        item['need'] = False
                    else:
                        item['need'] = True
            return slot_list
