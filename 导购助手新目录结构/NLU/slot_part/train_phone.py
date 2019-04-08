from __future__ import print_function
import os
import logging
import sys
from .networks.BiLSTM import BiLSTM
from .util.preprocessing import perpare_dataset
from .util.preprocessing import load_dataset_pickle


def train():
    """
    Multi-task train for three task:
    1. Computer slot task
    2. Phone slot task
    3. Camera slot task

    Model:
    BiLSTM-CRF with the share BiLSTM layer and share embedding(50)

    :return:
    """
    # :: Change into the working dir of the script ::
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # :: Logging level ::
    logging_level = logging.INFO
    logger = logging.getLogger()
    logger.setLevel(logging_level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging_level)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    datasets = {
        'computer':
            {'columns': {0: 'tokens', 1: 'computer_BIO'},
             'label': 'computer_BIO',
             'evaluate': True,
             'comment_symbol': None}
    }

    embeddings_path = 'wiki_100.utf8'

    # :: Prepares the data set to be used with the LSTM-network. Creates and stores cPickle files in the pkl/ folder ::
    pickle_file = perpare_dataset(embeddings_path, datasets)

    # Load the embeddings and the data set
    embeddings, mappings, data = load_dataset_pickle(pickle_file)

    # Some network hyper parameters
    params = {'classifier': ['CRF'], 'LSTM-Size': [100], 'dropout': (0.25, 0.25),
              'shareEmbeddings': True, 'shareEmbeddingsSize': 50,
              'preEmbeddings': True,
              'customClassifier': {'computer': ['CRF']}}

    # :: set the model ::
    model = BiLSTM(params)
    model.set_mappings(mappings, embeddings)
    model.set_dataset(datasets, data)
    model.model_save_path = "models/[model_name]_[DevScore]_[TestScore]_[Epoch].h5"
    model.sentence_result_path = 'sentence_result/'

    # :: train ::
    model.fit(epochs=100)


if __name__ == '__main__':
    # :: train and save the best model ::
    train()
