from __future__ import (division, absolute_import, print_function, unicode_literals)
import os
import numpy as np
import gzip
import os.path
import nltk
import logging
import re

from nltk import FreqDist

from .WordEmbeddings import word_normalize
from .CoNLL import read_conll

import sys
if (sys.version_info > (3, 0)):
    import pickle as pkl
else: #Python 2.7 imports
    import cPickle as pkl
    from io import open


def perpare_dataset(embeddings_path, datasets, frequency_threshold_unknown_tokens=50, reduce_pretrained_embeddings=False, val_transformations=None, pad_one_token_sentence=True):
    """
    Reads in the pre-trained embeddings (in text format) from embeddings_path and prepares those to be used with the LSTM network.
    Unknown words in the train_dataPath-file are added, if they appear at least frequency_threshold_unknown_tokens times
    
    # Arguments:
        embeddings_path: Full path to the pre-trained embeddings file. File must be in text format.
        dataset_files: Full path to the [train,dev,test]-file
        frequency_threshold_unknown_tokens: Unknown words are added, if they occure more than frequency_threshold_unknown_tokens times in the train set
        reduce_pretrained_embeddings: Set to true, then only the embeddings needed for training will be loaded
        val_transformations: Column specific value transformations
        pad_one_token_sentence: True to pad one sentence tokens (needed for CRF classifier)
    """
    embeddings_name = os.path.splitext(embeddings_path)[0]
    pkl_name = "_".join(sorted(datasets.keys()) + [embeddings_name])
    output_path = 'pkl/' + pkl_name + '.pkl'

    if os.path.isfile(output_path):
        logging.info("Using existent pickle file: %s" % output_path)
        return output_path

    casing2idx = get_casing_vocab()
    embeddings, word2idx = read_embeddings(embeddings_path, datasets, frequency_threshold_unknown_tokens, reduce_pretrained_embeddings)
    
    mappings = {'tokens': word2idx, 'casing': casing2idx}
    pkl_objects = {'embeddings': embeddings, 'mappings': mappings, 'datasets': datasets, 'data': {}}

    for dataset_name, dataset in datasets.items():
        dataset_columns = dataset['columns']
        comment_symbol = dataset['comment_symbol']

        train_data = 'data/%s/train.txt' % dataset_name
        dev_data = 'data/%s/dev.txt' % dataset_name
        test_data = 'data/%s/test.txt' % dataset_name
        paths = [train_data, dev_data, test_data]

        logging.info(":: Transform "+dataset_name+" dataset ::")
        pkl_objects['data'][dataset_name] = create_pkl_files(paths, mappings, dataset_columns, comment_symbol, val_transformations, pad_one_token_sentence)

    f = open(output_path, 'wb')
    pkl.dump(pkl_objects, f, -1)
    f.close()
    
    logging.info("DONE - Embeddings file saved: %s" % output_path)
    
    return output_path


def load_dataset_pickle(embeddingsPickle):
    """ Loads the cPickle file, that contains the word embeddings and the datasets """
    f = open(embeddingsPickle, 'rb')
    pkl_objects = pkl.load(f)
    f.close()

    return pkl_objects['embeddings'], pkl_objects['mappings'], pkl_objects['data']


def read_embeddings(embeddings_path, dataset_files, frequency_threshold_unknown_tokens, reduce_pretrained_embeddings):
    """
    Reads the embeddings_path.
    :param embeddings_path: File path to pretrained embeddings
    :param dataset_name:
    :param dataset_files:
    :param frequency_threshold_unknown_tokens:
    :param reduce_pretrained_embeddings:
    :return:
    """
    # Check that the embeddings file exists
    if not os.path.isfile(embeddings_path):
        if embeddings_path in ['komninos_english_embeddings.gz', 'levy_english_dependency_embeddings.gz', 'reimers_german_embeddings.gz']:
            get_embeddings(embeddings_path)
        else:
            print("The embeddings file %s was not found" % embeddings_path)
            exit()

    logging.info("Generate new embeddings files for a dataset")

    needed_vocab = {}
    if reduce_pretrained_embeddings:
        logging.info("Compute which tokens are required for the experiment")

        def create_dict(file_name, token_pos, vocab):
            for line in open(file_name):
                if line.startswith('#'):
                    continue
                splits = line.strip().split()
                if len(splits) > 1:
                    word = splits[token_pos]
                    word_lower = word.lower()
                    word_normalized = word_normalize(word_lower)

                    vocab[word] = True
                    vocab[word_lower] = True
                    vocab[word_normalized] = True

        for dataset_name, dataset in dataset_files.items():
            data_columns_idx = {y: x for x, y in dataset['columns'].items()}
            token_idx = data_columns_idx['tokens']
            dataset_path = 'data/%s/' % dataset_name

            for dataset_file_name in ['train.txt', 'dev.txt', 'test.txt']:
                create_dict(dataset_path + dataset_file_name, token_idx, needed_vocab)

    # :: Read in word embeddings ::
    logging.info("Read file: %s" % embeddings_path)
    word2idx = {}
    embeddings = []

    embeddings_in = gzip.open(embeddings_path, "rt", encoding='utf-8') if embeddings_path.endswith('.gz') else open(embeddings_path,
                                                                                               encoding="utf8")

    embeddings_dimension = None

    for line in embeddings_in:
        split = line.rstrip().split(" ")
        word = split[0]

        if embeddings_dimension == None:
            embeddings_dimension = len(split) - 1

        if (len(
                split) - 1) != embeddings_dimension:  # :: Assure that all lines in the embeddings file are of the same length
            print("ERROR: A line in the embeddings file had more or less  dimensions than expected. Skip token.")
            continue

        if len(word2idx) == 0:  # Add padding+unknown
            word2idx["PADDING_TOKEN"] = len(word2idx)
            vector = np.zeros(embeddings_dimension)
            embeddings.append(vector)

            word2idx["UNKNOWN_TOKEN"] = len(word2idx)
            vector = np.random.uniform(-0.25, 0.25, embeddings_dimension)  # Alternativ -sqrt(3/dim) ... sqrt(3/dim)
            embeddings.append(vector)

        vector = np.array([float(num) for num in split[1:]])

        if len(needed_vocab) == 0 or word in needed_vocab:
            if word not in word2idx:
                embeddings.append(vector)
                word2idx[word] = len(word2idx)

    # Extend embeddings file with new tokens
    def createFD(file_name, token_index, fd, word2idx):
        for line in open(file_name, encoding='utf-8'):
            if line.startswith('#'):
                continue

            splits = line.strip().split()

            if len(splits) > 1:
                word = splits[token_index]
                word_lower = word.lower()
                word_normalized = word_normalize(word_lower)

                if word not in word2idx and word_lower not in word2idx and word_normalized not in word2idx:
                    fd[word_normalized] += 1

    if frequency_threshold_unknown_tokens != None and frequency_threshold_unknown_tokens >= 0:
        fd = nltk.FreqDist()
        for dataset_name, datasetFile in dataset_files.items():
            data_columns_idx = {y: x for x, y in datasetFile['columns'].items()}
            token_idx = data_columns_idx['tokens']
            dataset_path = 'data/%s/' % dataset_name
            createFD(dataset_path + 'train.txt', token_idx, fd, word2idx)

        added_words = 0
        for word, freq in fd.most_common(10000):
            if freq < frequency_threshold_unknown_tokens:
                break

            added_words += 1
            word2idx[word] = len(word2idx)
            vector = np.random.uniform(-0.25, 0.25, len(split) - 1)  # Alternativ -sqrt(3/dim) ... sqrt(3/dim)
            embeddings.append(vector)

            assert (len(word2idx) == len(embeddings))

        logging.info("Added words: %d" % added_words)
    embeddings = np.array(embeddings)

    return embeddings, word2idx


def read_embeddings_from_wiki(embeddings_path, dataset_files, frequency_threshold_unknown_tokens, reduce_pretrained_embeddings):
    """
    Reads the embeddings_path.
    :param embeddings_path: File path to pretrained embeddings
    :param dataset_name:
    :param dataset_files:
    :param frequency_threshold_unknown_tokens:
    :param reduce_pretrained_embeddings:
    :return:
    """
    # Check that the embeddings file exists
    if not os.path.isfile(embeddings_path):
        if embeddings_path in ['komninos_english_embeddings.gz', 'levy_english_dependency_embeddings.gz', 'reimers_german_embeddings.gz']:
            get_embeddings(embeddings_path)
        else:
            print("The embeddings file %s was not found" % embeddings_path)
            exit()

    logging.info("Generate new embeddings files for a dataset")

    needed_vocab = {}
    if reduce_pretrained_embeddings:
        logging.info("Compute which tokens are required for the experiment")

        def create_dict(file_name, token_pos, vocab):
            for line in open(file_name):
                if line.startswith('#'):
                    continue
                splits = line.strip().split()
                if len(splits) > 1:
                    word = splits[token_pos]
                    word_lower = word.lower()
                    word_normalized = word_normalize(word_lower)

                    vocab[word] = True
                    vocab[word_lower] = True
                    vocab[word_normalized] = True

        for dataset_name, dataset in dataset_files.items():
            data_columns_idx = {y: x for x, y in dataset['columns'].items()}
            token_idx = data_columns_idx['tokens']
            dataset_path = 'data/%s/' % dataset_name

            for dataset_file_name in ['train.txt', 'dev.txt', 'test.txt']:
                create_dict(dataset_path + dataset_file_name, token_idx, needed_vocab)

    # :: Read in word embeddings ::
    logging.info("Read file: %s" % embeddings_path)
    word2idx = {}
    embeddings = []

    embeddings_in = gzip.open(embeddings_path, "rt", encoding='utf-8') if embeddings_path.endswith('.gz') else open(embeddings_path,
                                                                                               encoding="utf8")

    embeddings_dimension = None

    for line in embeddings_in:
        split = line.rstrip().split(" ")
        word = split[0]

        if embeddings_dimension == None:
            embeddings_dimension = len(split) - 1

        if (len(
                split) - 1) != embeddings_dimension:  # Assure that all lines in the embeddings file are of the same length
            print("ERROR: A line in the embeddings file had more or less  dimensions than expected. Skip token.")
            continue

        if len(word2idx) == 0:  # Add padding+unknown
            word2idx["PADDING_TOKEN"] = len(word2idx)
            vector = np.zeros(embeddings_dimension)
            embeddings.append(vector)

            word2idx["UNKNOWN_TOKEN"] = len(word2idx)
            vector = np.random.uniform(-0.25, 0.25, embeddings_dimension)  # Alternativ -sqrt(3/dim) ... sqrt(3/dim)
            embeddings.append(vector)

        vector = np.array([float(num) for num in split[1:]])

        if len(needed_vocab) == 0 or word in needed_vocab:
            if word not in word2idx:
                embeddings.append(vector)
                word2idx[word] = len(word2idx)

    # Extend embeddings file with new tokens
    def createFD(file_name, token_index, fd, word2idx):
        for line in open(file_name):
            if line.startswith('#'):
                continue

            splits = line.strip().split()

            if len(splits) > 1:
                word = splits[token_index]
                word_lower = word.lower()
                word_normalized = word_normalize(word_lower)

                if word not in word2idx and word_lower not in word2idx and word_normalized not in word2idx:
                    fd[word_normalized] += 1

    if frequency_threshold_unknown_tokens != None and frequency_threshold_unknown_tokens >= 0:
        fd = nltk.FreqDist()
        for dataset_name, datasetFile in dataset_files.items():
            data_columns_idx = {y: x for x, y in datasetFile['columns'].items()}
            token_idx = data_columns_idx['tokens']
            dataset_path = 'data/%s/' % dataset_name
            createFD(dataset_path + 'train.txt', token_idx, fd, word2idx)

        added_words = 0
        for word, freq in fd.most_common(10000):
            if freq < frequency_threshold_unknown_tokens:
                break

            added_words += 1
            word2idx[word] = len(word2idx)
            vector = np.random.uniform(-0.25, 0.25, len(split) - 1)  # Alternativ -sqrt(3/dim) ... sqrt(3/dim)
            embeddings.append(vector)

            assert (len(word2idx) == len(embeddings))

        logging.info("Added words: %d" % added_words)
    embeddings = np.array(embeddings)

    return embeddings, word2idx


def add_char_information(sentences):
    """Breaks every token into the characters"""
    for sentence_idx in range(len(sentences)):
        sentences[sentence_idx]['characters'] = []
        for token_idx in range(len(sentences[sentence_idx]['tokens'])):
            token = sentences[sentence_idx]['tokens'][token_idx]
            chars = [c for c in token]
            sentences[sentence_idx]['characters'].append(chars)


def add_casing_information(sentences):
    """Adds information of the casing of words"""
    for sentence_idx in range(len(sentences)):
        sentences[sentence_idx]['casing'] = []
        for token_idx in range(len(sentences[sentence_idx]['tokens'])):
            token = sentences[sentence_idx]['tokens'][token_idx]
            sentences[sentence_idx]['casing'].append(get_casing(token))
       
       
def get_casing(word):
    """Returns the casing for a word"""
    casing = 'other'
    
    num_digits = 0
    for char in word:
        if char.isdigit():
            num_digits += 1
            
    digit_fraction = num_digits / float(len(word))
    
    if word.isdigit():  # :: Is a digit ::
        casing = 'numeric'
    elif digit_fraction > 0.5:
        casing = 'mainly_numeric'
    elif word.islower():  # :: All lower case ::
        casing = 'allLower'
    elif word.isupper():  # :: All upper case ::
        casing = 'allUpper'
    elif word[0].isupper():  # :: is a title, initial char upper, then all lower ::
        casing = 'initialUpper'
    elif num_digits > 0:
        casing = 'contains_digit'
    
    return casing

def get_casing_vocab():
    entries = ['PADDING', 'other', 'numeric', 'mainly_numeric', 'allLower', 'allUpper', 'initialUpper', 'contains_digit']
    return {entries[idx]: idx for idx in range(len(entries))}


def create_matrices(sentences, mappings, pad_one_token_sentence):
    data = []
    num_tokens = 0
    num_unknown_tokens = 0
    missing_tokens = FreqDist()
    padded_sentences = 0

    for sentence in sentences:
        row = {name: [] for name in list(mappings.keys())+['raw_tokens']}
        
        for mapping, str2Idx in mappings.items():    
            if mapping not in sentence:
                continue
                    
            for entry in sentence[mapping]:                
                if mapping.lower() == 'tokens':
                    num_tokens += 1
                    idx = str2Idx['UNKNOWN_TOKEN']
                    
                    if entry in str2Idx:
                        idx = str2Idx[entry]
                    elif entry.lower() in str2Idx:
                        idx = str2Idx[entry.lower()]
                    elif word_normalize(entry) in str2Idx:
                        idx = str2Idx[word_normalize(entry)]
                    else:
                        num_unknown_tokens += 1
                        missing_tokens[word_normalize(entry)] += 1
                        
                    row['raw_tokens'].append(entry)
                elif mapping.lower() == 'characters':  
                    idx = []
                    for c in entry:
                        if c in str2Idx:
                            idx.append(str2Idx[c])
                        else:
                            idx.append(str2Idx['UNKNOWN'])                           
                                      
                else:
                    idx = str2Idx[entry]
                                    
                row[mapping].append(idx)
                
        if len(row['tokens']) == 1 and pad_one_token_sentence:
            padded_sentences += 1
            for mapping, str2Idx in mappings.items():
                if mapping.lower() == 'tokens':
                    row['tokens'].append(mappings['tokens']['PADDING_TOKEN'])
                    row['raw_tokens'].append('PADDING_TOKEN')
                elif mapping.lower() == 'characters':
                    row['characters'].append([0])
                else:
                    row[mapping].append(0)
            
        data.append(row)
    
    if num_tokens > 0:
        logging.info("Unknown-Tokens: %.2f%%" % (num_unknown_tokens/float(num_tokens)*100))
        
    return data

  
def create_pkl_files(dataset_files, mappings, cols, comment_symbol, val_transformation, pad_one_token_sentence):
    train_sentences = read_conll(dataset_files[0], cols, comment_symbol, val_transformation)
    dev_sentences = read_conll(dataset_files[1], cols, comment_symbol, val_transformation)
    test_sentences = read_conll(dataset_files[2], cols, comment_symbol, val_transformation)

    extend_mappings(mappings, train_sentences+dev_sentences+test_sentences)

    charset = {"PADDING":0, "UNKNOWN":1}
    for c in " 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,-_()[]{}!?:;#'\"/\\%$`&=*+@^~|":
        charset[c] = len(charset)
    mappings['characters'] = charset
    
    add_char_information(train_sentences)
    add_casing_information(train_sentences)
    
    add_char_information(dev_sentences)
    add_casing_information(dev_sentences)
    
    add_char_information(test_sentences)
    add_casing_information(test_sentences)

    logging.info(":: Create Train Matrix ::")
    train_matrix = create_matrices(train_sentences, mappings, pad_one_token_sentence)

    logging.info(":: Create Dev Matrix ::")
    dev_matrix = create_matrices(dev_sentences, mappings, pad_one_token_sentence)

    logging.info(":: Create Test Matrix ::")
    test_matrix = create_matrices(test_sentences, mappings, pad_one_token_sentence)

    data = {
                'train_matrix': train_matrix,
                'dev_matrix': dev_matrix,
                'test_matrix': test_matrix
            }        

    return data


def extend_mappings(mappings, sentences):
    sentence_keys = list(sentences[0].keys())
    sentence_keys.remove('tokens') #No need to map tokens

    for sentence in sentences:
        for name in sentence_keys:
            if name not in mappings:
                mappings[name] = {'O':0} #'O' is also used for padding

            for item in sentence[name]:              
                if item not in mappings[name]:
                    mappings[name][item] = len(mappings[name])


def get_embeddings(name):
    if not os.path.isfile(name):
        download("https://public.ukp.informatik.tu-darmstadt.de/reimers/embeddings/"+name)


def get_levy_dependency_embeddings():
    """
    Downloads from https://levyomer.wordpress.com/2014/04/25/dependency-based-word-embeddings/
    the dependency based word embeddings and unzips them    
    """ 
    if not os.path.isfile("levy_deps.words.bz2"):
        print("Start downloading word embeddings from Levy et al. ...")
        os.system("wget -O levy_deps.words.bz2 http://u.cs.biu.ac.il/~yogo/data/syntemb/deps.words.bz2")
    
    print("Start unzip word embeddings ...")
    os.system("bzip2 -d levy_deps.words.bz2")


def get_reimers_embeddings():
    """
    Downloads from https://www.ukp.tu-darmstadt.de/research/ukp-in-challenges/germeval-2014/
    embeddings for German
    """
    if not os.path.isfile("2014_tudarmstadt_german_50mincount.vocab.gz"):
        print("Start downloading word embeddings from Reimers et al. ...")
        os.system("wget https://public.ukp.informatik.tu-darmstadt.de/reimers/2014_german_embeddings/2014_tudarmstadt_german_50mincount.vocab.gz")
    

if sys.version_info >= (3,):
    import urllib.request as urllib2
    import urllib.parse as urlparse
    from urllib.request import urlretrieve
else:
    import urllib2
    import urlparse
    from urllib import urlretrieve


def download(url, destination=os.curdir, silent=False):
    file_name = os.path.basename(urlparse.urlparse(url).path) or 'downloaded.file'

    def get_size():
        meta = urllib2.urlopen(url).info()
        meta_func = meta.getheaders if hasattr(
            meta, 'getheaders') else meta.get_all
        meta_length = meta_func('Content-Length')
        try:
            return int(meta_length[0])
        except:
            return 0

    def kb_to_mb(kb):
        return kb / 1024.0 / 1024.0

    def callback(blocks, block_size, total_size):
        current = blocks * block_size
        percent = 100.0 * current / total_size
        line = '[{0}{1}]'.format(
            '=' * int(percent / 2), ' ' * (50 - int(percent / 2)))
        status = '\r{0:3.0f}%{1} {2:3.1f}/{3:3.1f} MB'
        sys.stdout.write(
            status.format(
                percent, line, kb_to_mb(current), kb_to_mb(total_size)))

    path = os.path.join(destination, file_name)

    logging.info(
        'Downloading: {0} ({1:3.1f} MB)'.format(url, kb_to_mb(get_size())))
    try:
        (path, headers) = urlretrieve(url, path, None if silent else callback)
    except:
        os.remove(path)
        raise Exception("Can't download {0}".format(path))
    else:
        print()
        logging.info('Downloaded to: {0}'.format(path))

    return path


def clean(text):
    text = re.sub(r' ', '', text)
    # text = re.sub(r'[’!"#$%&\'()*+,-/:;<=>@,。★、…【】《》“”‘’！^_`{|}~]+', '', text)
    text = text.lower()

    return text


def transform_digital(text):
    sequence = re.sub(r'\d', 'x', text)
    sequence = re.sub(r'[一二三四五六七八九十零百千]', 'x', sequence)
    sequence = re.sub(r'x[.]x', 'xxx', sequence)
    sequence = sequence.lower()
    return sequence