# -*- coding: utf-8 -*
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from xgboost.sklearn import XGBClassifier
import jieba
from sklearn import metrics
from sklearn.model_selection import train_test_split
import pickle


def clean(text):
    """
    Pre-processing for the text
    :param text:
    :return: the pre-process text
    """

    text = re.sub(r' ', '', text)
    text = re.sub(r'[’!"#$%&\'()*+,-/:;<=>@,。★、【】《》“”‘’！^_`{|}~]+', '', text)
    clean_words = []
    for word in jieba.cut(text):
        clean_words.append(word)
    return ' '.join(clean_words)


def train():
    """
    Train model and save model:
    feature: tf_idf
    Classifier: XGBClassifier
    Model path: './model'
    :return:
    """

    print('read data...')
    data = pd.read_csv('./data/intend_data_1.csv')
    data = data.sample(frac=1.0, replace=True, random_state=42)

    print('clean data...')
    data['sentence'] = data['sentence'].apply(clean)

    label_subject = dict(zip(range(0, len(set(data['label']))), sorted(list(set(data['label'])))))
    subject_label = dict(zip(sorted(list(set(data['label']))), range(0, len(set(data['label'])))))

    data['label'] = data['label'].map(subject_label)

    X_train, X_test, y_train, y_test = train_test_split(list(data['sentence']), list(data['label']), test_size=0.1, random_state=42)


    print('extract tfidf feature')
    vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2))

    tfidf_model = vec.fit(data['sentence'].tolist())
    trn_term_doc = tfidf_model.transform(X_train)
    test_term_doc = tfidf_model.transform(X_test)

    print('train topic model')
    classifier_model = XGBClassifier(learning_rate=0.30,
                              n_estimators=300,
                              max_depth=5,
                              objective='multi:softmax',
                              seed=42)

    classifier_model.fit(trn_term_doc, y_train, eval_metric='mlogloss')

    train_preds = classifier_model.predict(trn_term_doc)
    print('result in train:')
    print(metrics.classification_report(y_train, train_preds))

    test_preds = classifier_model.predict(test_term_doc)
    print('result in train:')
    print(metrics.classification_report(y_test, test_preds))
    print('train semantic model end')

    with open('./model/model.pk', 'wb') as file:
        save = {
            'label_subject': label_subject,
            'tfidfVectorizer': tfidf_model,
            'classifier_model': classifier_model
        }
        pickle.dump(save, file)


def evaluate():
    """
    The evaluate part:

    :return:
    """
    with open('./model/model.pk', 'rb') as fr:
        save = pickle.load(fr)
        tfidf_model = save['tfidfVectorizer']
        classifier_model = save['classifier_model']
        label_subject = save['label_subject']
    while True:
        sentence = input()
        sentence = clean(sentence)
        sentence_list = [sentence]
        sentence_term_doc = tfidf_model.transform(sentence_list)
        label = classifier_model.predict(sentence_term_doc)
        print(label_subject[label[0]])


if __name__ == "__main__":
    train()
    # evaluate()