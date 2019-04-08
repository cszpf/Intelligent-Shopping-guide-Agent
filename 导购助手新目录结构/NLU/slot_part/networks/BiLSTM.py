"""
A bidirectional LSTM with optional CRF and character-based presentation for NLP sequence tagging used for multi-task learning.
"""

from __future__ import print_function
from ..util import BIOF1Validation

import keras
from keras.optimizers import *
from keras.models import Model
from keras.layers import *
import math
import numpy as np
import sys
import time
import os
import random
import logging

from .keraslayers.ChainCRF import ChainCRF


class BiLSTM:

    def __init__(self, params=None):
        self.models = None
        self.model_save_path = None
        self.results_save_path = None
        self.sentence_result_path = None

        # Hyper parameters for the network
        default_params = {'dropout': (0.5,0.5), 'classifier': ['Softmax'], 'LSTM-Size': (100,), 'customClassifier': {},
                         'optimizer': 'adam',
                         'char_embeddings': None, 'char_embeddings_size': 30, 'char_filter_size': 30, 'char_filter_length': 3, 'char_LSTM_size': 25, 'max_char_length': 25,
                         'useTaskIdentifier': False, 'clipvalue': 0, 'clipnorm': 1,
                         'earlyStopping': 10, 'miniBatchSize': 32,
                         'feature_names': ['tokens'], 'addFeatureDimensions': 10,
                         'shareEmbeddings': False, 'shareEmbeddingsSize': 50
                         }
        if params != None:
            default_params.update(params)
        self.params = default_params



    def set_mappings(self, mappings, embeddings):
        self.embeddings = embeddings
        self.mappings = mappings

    def set_dataset(self, datasets, data):
        self.datasets = datasets
        self.data = data

        # Create some helping variables
        self.main_model_name = None
        self.epoch = 0
        self.learning_rate_updates = {'sgd': {1: 0.1, 3: 0.05, 5: 0.01}}
        self.model_names = list(self.datasets.keys())
        self.evaluate_model_names = []
        self.label_keys = {}
        self.idx2labels = {}
        self.trainmini_batch_ranges = None
        self.train_sentence_length_ranges = None


        for model_name in self.model_names:
            label_key = self.datasets[model_name]['label']
            self.label_keys[model_name] = label_key
            self.idx2labels[model_name] = {v: k for k, v in self.mappings[label_key].items()}
            
            if self.datasets[model_name]['evaluate']:
                self.evaluate_model_names.append(model_name)
            
            logging.info("--- %s ---" % model_name)
            logging.info("%d train sentences" % len(self.data[model_name]['train_matrix']))
            logging.info("%d dev sentences" % len(self.data[model_name]['dev_matrix']))
            logging.info("%d test sentences" % len(self.data[model_name]['test_matrix']))
            
        
        if len(self.evaluate_model_names) == 1:
            self.main_model_name = self.evaluate_model_names[0]
             
        self.casing2idx = self.mappings['casing']

        if self.params['char_embeddings'] not in [None, "None", "none", False, "False", "false"]:
            logging.info("Pad words to uniform length for characters embeddings")
            all_sentences = []
            for dataset in self.data.values():
                for data in [dataset['train_matrix'], dataset['dev_matrix'], dataset['test_matrix']]:
                    for sentence in data:
                        all_sentences.append(sentence)

            self.pad_characters(all_sentences)
            logging.info("Words padded to %d characters" % (self.max_char_len))

    def build_model(self):
        self.models = {}

        tokens_input = Input(shape=(None,), dtype='int32', name='words_input')

        input_nodes = [tokens_input]
        merge_input_layers = []

        if self.params['preEmbeddings'] == True:
            pre_tokens = Embedding(input_dim=self.embeddings.shape[0], output_dim=self.embeddings.shape[1], weights=[self.embeddings], trainable=False, name='word_embeddings')(tokens_input)
            merge_input_layers.append(pre_tokens)

        if self.params['shareEmbeddings'] == True:
            embedding_share = Embedding(input_dim=self.embeddings.shape[0], output_dim=int(self.params['shareEmbeddingsSize']), trainable=True, name='word_trainable_embeddings')
            tokens_share = embedding_share(tokens_input)
            merge_input_layers.append(tokens_share)
        
        if len(merge_input_layers) >= 2:
            merged_input = concatenate(merge_input_layers)
        else:
            merged_input = merge_input_layers[0]
        
        # Add LSTMs
        shared_layer = merged_input
        logging.info("LSTM-Size: %s" % str(self.params['LSTM-Size']))
        cnt = 1
        for size in self.params['LSTM-Size']:      
            if isinstance(self.params['dropout'], (list, tuple)):  
                shared_layer = Bidirectional(LSTM(size, return_sequences=True,
                                                  dropout=self.params['dropout'][0],
                                                  recurrent_dropout=self.params['dropout'][1]),
                                             name='shared_varLSTM_'+str(cnt))(shared_layer)
            else:
                """ Naive dropout """
                shared_layer = Bidirectional(LSTM(size, return_sequences=True),
                                             name='shared_LSTM_'+str(cnt))(shared_layer) 
                if self.params['dropout'] > 0.0:
                    shared_layer = TimeDistributed(Dropout(self.params['dropout']),name='shared_dropout_'+str(self.params['dropout'])+"_"+str(cnt))(shared_layer)
            
            cnt += 1
            
        for model_name in self.model_names:
            output = shared_layer
            
            model_classifier = self.params['customClassifier'][model_name] if model_name in self.params['customClassifier'] else self.params['classifier']

            if not isinstance(model_classifier, (tuple, list)):
                model_classifier = [model_classifier]
            
            cnt = 1
            for classifier in model_classifier:
                n_class_labels = len(self.mappings[self.label_keys[model_name]])

                if classifier == 'Softmax':
                    output = TimeDistributed(Dense(n_class_labels, activation='softmax'), name=model_name+'_softmax')(output)
                    loss_fct = 'sparse_categorical_crossentropy'
                elif classifier == 'CRF':
                    output = TimeDistributed(Dense(n_class_labels, activation=None),
                                             name=model_name + '_hidden_lin_layer')(output)
                    crf = ChainCRF(name=model_name+'_crf')
                    output = crf(output)
                    loss_fct = crf.sparse_loss
                elif isinstance(classifier, (list, tuple)) and classifier[0] == 'LSTM':
                            
                    size = classifier[1]
                    if isinstance(self.params['dropout'], (list, tuple)): 
                        output = Bidirectional(LSTM(size, return_sequences=True, dropout=self.params['dropout'][0], recurrent_dropout=self.params['dropout'][1]), name=model_name+'_varLSTM_'+str(cnt))(output)
                    else:
                        """ Naive dropout """ 
                        output = Bidirectional(LSTM(size, return_sequences=True), name=model_name+'_LSTM_'+str(cnt))(output) 
                        if self.params['dropout'] > 0.0:
                            output = TimeDistributed(Dropout(self.params['dropout']), name=model_name+'_dropout_'+str(self.params['dropout'])+"_"+str(cnt))(output)                    
                else:
                    assert(False)  # Wrong classifier
                    
                cnt += 1
                
            # :: Parameters for the optimizer ::
            optimizer_params = {}
            if 'clipnorm' in self.params and self.params['clipnorm'] != None and  self.params['clipnorm'] > 0:
                optimizer_params['clipnorm'] = self.params['clipnorm']
            
            if 'clipvalue' in self.params and self.params['clipvalue'] != None and  self.params['clipvalue'] > 0:
                optimizer_params['clipvalue'] = self.params['clipvalue']
            
            if self.params['optimizer'].lower() == 'adam':
                opt = Adam(**optimizer_params)
            elif self.params['optimizer'].lower() == 'nadam':
                opt = Nadam(**optimizer_params)
            elif self.params['optimizer'].lower() == 'rmsprop': 
                opt = RMSprop(**optimizer_params)
            elif self.params['optimizer'].lower() == 'adadelta':
                opt = Adadelta(**optimizer_params)
            elif self.params['optimizer'].lower() == 'adagrad':
                opt = Adagrad(**optimizer_params)
            elif self.params['optimizer'].lower() == 'sgd':
                opt = SGD(lr=0.1, **optimizer_params)
            
            
            model = Model(inputs=input_nodes, outputs=[output])
            model.compile(loss=loss_fct, optimizer=opt)
            
            model.summary(line_length=125)
            
            self.models[model_name] = model
        
    def train_model(self):
        self.epoch += 1
        
        if self.params['optimizer'] in self.learning_rate_updates and self.epoch in self.learning_rate_updates[self.params['optimizer']]:       
            logging.info("Update Learning Rate to %f" % (self.learning_rate_updates[self.params['optimizer']][self.epoch]))
            for model_name in self.model_names:            
                K.set_value(self.models[model_name].optimizer.lr, self.learning_rate_updates[self.params['optimizer']][self.epoch]) 

        for batch in self.mini_batch_iterate_dataset():
            for model_name in self.model_names:         
                nn_labels = batch[model_name][0]
                nn_input = batch[model_name][1:2]
                self.models[model_name].train_on_batch(nn_input, nn_labels)
                 
    def mini_batch_iterate_dataset(self, model_names=None):
        """ Create based on sentence length mini-batches with approx. the same size. Sentences and 
        mini-batch chunks are shuffled and used to the train the model """

        if self.train_sentence_length_ranges == None:
            """ Create mini batch ranges """

            self.train_sentence_length_ranges = {}
            self.trainmini_batch_ranges = {}            
            for model_name in self.model_names:
                train_data = self.data[model_name]['train_matrix']
                train_data.sort(key=lambda x:len(x['tokens']))  # Sort train matrix by sentence length
                train_ranges = []
                old_sent_length = len(train_data[0]['tokens'])            
                idx_start = 0
                
                # Find start and end of ranges with sentences with same length
                for idx in range(len(train_data)):
                    sent_length = len(train_data[idx]['tokens'])
                    
                    if sent_length != old_sent_length:
                        train_ranges.append((idx_start, idx))
                        idx_start = idx
                    
                    old_sent_length = sent_length
                
                # Add last sentence
                train_ranges.append((idx_start, len(train_data)))
                
                
                # Break up ranges into smaller mini batch sizes
                mini_batch_ranges = []
                for batch_range in train_ranges:
                    range_len = batch_range[1]-batch_range[0]

                    bins = int(math.ceil(range_len/float(self.params['miniBatchSize'])))
                    bin_size = int(math.ceil(range_len / float(bins)))
                    
                    for bin_nr in range(bins):
                        start_idx = bin_nr*bin_size+batch_range[0]
                        end_idx = min(batch_range[1],(bin_nr+1)*bin_size+batch_range[0])
                        mini_batch_ranges.append((start_idx, end_idx))
                      
                self.train_sentence_length_ranges[model_name] = train_ranges
                self.trainmini_batch_ranges[model_name] = mini_batch_ranges
                
        if model_names == None:
            model_names = self.model_names
            
        # Shuffle training data
        for model_name in model_names:      
            # 1. Shuffle sentences that have the same length
            x = self.data[model_name]['train_matrix']
            for data_range in self.train_sentence_length_ranges[model_name]:
                for i in reversed(range(data_range[0]+1, data_range[1])):
                    # pick an element in x[:i+1] with which to exchange x[i]
                    j = random.randint(data_range[0], i)
                    x[i], x[j] = x[j], x[i]
               
            # 2. Shuffle the order of the mini batch ranges       
            random.shuffle(self.trainmini_batch_ranges[model_name])
     
        
        # Iterate over the mini batch ranges
        if self.main_model_name != None:
            range_length = len(self.trainmini_batch_ranges[self.main_model_name])
        else:
            range_length = min([len(self.trainmini_batch_ranges[model_name]) for model_name in model_names])

        
        batches = {}
        for idx in range(range_length):
            batches.clear()
            
            for model_name in model_names:   
                train_matrix = self.data[model_name]['train_matrix']
                data_range = self.trainmini_batch_ranges[model_name][idx % len(self.trainmini_batch_ranges[model_name])] 
                labels = np.asarray([train_matrix[idx][self.label_keys[model_name]] for idx in range(data_range[0], data_range[1])])
                labels = np.expand_dims(labels, -1)
                
                
                batches[model_name] = [labels]
                
                for feature_name in self.params['feature_names']:
                    input_data = np.asarray([train_matrix[idx][feature_name] for idx in range(data_range[0], data_range[1])])
                    batches[model_name].append(input_data)
            
            yield batches

    def store_results(self, results_file_path):
        if results_file_path != None:
            directory = os.path.dirname(results_file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                
            self.results_save_path = open(results_file_path, 'w')
        else:
            self.results_save_path = None
        
    def fit(self, epochs):
        if self.models is None:
            self.build_model()

        total_train_time = 0
        max_dev_score = {model_name: 0 for model_name in self.models.keys()}
        max_test_score = {model_name: 0 for model_name in self.models.keys()}
        max_epoch = {model_name: 0 for model_name in self.models.keys()}
        no_improvement_since = 0
        for epoch in range(epochs):      
            sys.stdout.flush()           
            logging.info("\n--------- Epoch %d -----------" % (epoch+1))
            
            start_time = time.time() 
            self.train_model()
            time_diff = time.time() - start_time
            total_train_time += time_diff
            logging.info("%.2f sec for training (%.2f total)" % (time_diff, total_train_time))
            
            
            start_time = time.time() 
            for model_name in self.evaluate_model_names:
                logging.info("-- %s --" % (model_name))
                dev_score, test_score = self.compute_score(model_name, self.data[model_name]['dev_matrix'], self.data[model_name]['test_matrix'])
         
                
                if dev_score > max_dev_score[model_name]:
                    max_dev_score[model_name] = dev_score
                    max_test_score[model_name] = test_score
                    max_epoch[model_name] = epoch
                    no_improvement_since = 0

                    # :: Save the model ::
                    if self.model_save_path != None:
                        self.save_model(model_name, epoch, dev_score, test_score)
                else:
                    no_improvement_since += 1
                    
                    
                if self.results_save_path != None:
                    self.results_save_path.write("\t".join(map(str, [epoch + 1, model_name, dev_score, test_score, max_dev_score[model_name], max_test_score[model_name]])))
                    self.results_save_path.write("\n")
                    self.results_save_path.flush()
                
                logging.info("\nScores from epoch with best dev-scores:\n  Dev-Score: %.4f\n  Test-Score %.4f" % (max_dev_score[model_name], max_test_score[model_name]))
                logging.info("")
                
            logging.info("%.2f sec for evaluation" % (time.time() - start_time))
            
            if self.params['earlyStopping']  > 0 and no_improvement_since >= self.params['earlyStopping']:
                logging.info("!!! Early stopping, no improvement after "+str(no_improvement_since)+" epochs !!!")
                break

        for model_name in self.evaluate_model_names:
            dev_score = max_dev_score[model_name]
            test_score = max_test_score[model_name]
            epoch = max_epoch[model_name]
            model_path = self.model_save_path.replace("[DevScore]", "%.4f" % dev_score).replace("[TestScore]", "%.4f" % test_score).replace("[Epoch]", str(epoch+1)).replace("[model_name]", model_name)
            model = self.load_model(model_path).models[model_name]

            padded_pred_labels = self.predict_labels(model, self.data[model_name]['test_matrix'])
            self.write_result_in_file(model_name, 'test', padded_pred_labels, dev_score, test_score)

    def tag_sentences(self, sentences):
        # Pad characters
        if 'characters' in self.params['feature_names']:
            self.pad_characters(sentences)

        labels = {}
        for model_name, model in self.models.items():
            padded_pred_labels = self.predict_labels(model, sentences)
            pred_labels = []
            for idx in range(len(sentences)):
                unpadded_pred_labels = []
                for token_idx in range(len(sentences[idx]['tokens'])):
                    if sentences[idx]['tokens'][token_idx] != 0:  # Skip padding tokens
                        unpadded_pred_labels.append(padded_pred_labels[idx][token_idx])

                pred_labels.append(unpadded_pred_labels)

            idx2label = self.idx2labels[model_name]
            labels[model_name] = [[idx2label[tag] for tag in tag_sentence] for tag_sentence in pred_labels]

        return labels
            
    def get_sentence_lengths(self, sentences):
        sentence_lengths = {}
        for idx in range(len(sentences)):
            sentence = sentences[idx]['tokens']
            if len(sentence) not in sentence_lengths:
                sentence_lengths[len(sentence)] = []
            sentence_lengths[len(sentence)].append(idx)
        
        return sentence_lengths

    def predict_labels(self, model, sentences):
        pred_labels = [None]*len(sentences)
        sentence_lengths = self.get_sentence_lengths(sentences)
        
        for indices in sentence_lengths.values():
            nn_input = []                  
            for feature_name in self.params['feature_names']:
                input_data = np.asarray([sentences[idx][feature_name] for idx in indices])
                nn_input.append(input_data)
            
            predictions = model.predict(nn_input, verbose=False)
            predictions = predictions.argmax(axis=-1)  # Predict classes
           
            
            pred_idx = 0
            for idx in indices:
                pred_labels[idx] = predictions[pred_idx]    
                pred_idx += 1
        return pred_labels
   
    def compute_score(self, model_name, dev_matrix, test_matrix):
        if self.label_keys[model_name].endswith('_BIO') or self.label_keys[model_name].endswith('_IOBES') or self.label_keys[model_name].endswith('_IOB'):
            return self.compute_f1_scores(model_name, dev_matrix, test_matrix)
        else:
            return self.compute_acc_scores(model_name, dev_matrix, test_matrix)   

    def compute_f1_scores(self, model_name, dev_matrix, test_matrix):

        dev_pre, dev_rec, dev_f1 = self.compute_f1(model_name, dev_matrix)
        logging.info("Dev-Data: Prec: %.3f, Rec: %.3f, F1: %.4f" % (dev_pre, dev_rec, dev_f1))
        
        test_pre, test_rec, test_f1 = self.compute_f1(model_name, test_matrix)
        logging.info("Test-Data: Prec: %.3f, Rec: %.3f, F1: %.4f" % (test_pre, test_rec, test_f1))
        
        return dev_f1, test_f1
    
    def compute_acc_scores(self, model_name, dev_matrix, test_matrix):
        dev_acc = self.compute_acc(model_name, dev_matrix)
        test_acc = self.compute_acc(model_name, test_matrix)
        
        logging.info("Dev-Data: Accuracy: %.4f" % (dev_acc))
        logging.info("Test-Data: Accuracy: %.4f" % (test_acc))
        
        return dev_acc, test_acc   

    def write_result_in_file(self, model_name, data_name, pred_labels, dev_score, test_score):
        print('write best result infile...')
        path = self.sentence_result_path + model_name + '_' + data_name + '_dev_score_' + str(dev_score) + '_test_score_' + str(test_score) +'_result.txt'
        idx2labels = self.idx2labels
        sentences = []
        correct_labels = []
        datas = self.data[model_name][data_name + '_matrix']
        label_name = self.label_keys[model_name]

        for data in datas:
            sentences.append(data['raw_tokens'])
            correct_labels.append(data[label_name])
        with open(path, 'w', encoding='utf-8') as fout:
            for sentence, correctLabel, predLabel in zip(sentences, correct_labels, pred_labels):
                for id, word in enumerate(sentence):
                    fout.writelines(word + ' ' + idx2labels[model_name][correctLabel[id]] + ' ' + idx2labels[model_name][predLabel[id]])
                    fout.writelines('\n')
                fout.writelines('\n')

    def compute_f1(self, model_name, sentences):
        label_key = self.label_keys[model_name]
        model = self.models[model_name]
        idx2label = self.idx2labels[model_name]
        
        correct_labels = [sentences[idx][label_key] for idx in range(len(sentences))]
        pred_labels = self.predict_labels(model, sentences) 

        label_key = self.label_keys[model_name]
        encoding_scheme = label_key[label_key.index('_')+1:]
        pre, rec, f1 = BIOF1Validation.compute_f1(pred_labels, correct_labels, idx2label, 'O', encoding_scheme)
        pre_b, rec_b, f1_b = BIOF1Validation.compute_f1(pred_labels, correct_labels, idx2label, 'B', encoding_scheme)
        
        if f1_b > f1:
            logging.debug("Setting wrong tags to B- improves from %.4f to %.4f" % (f1, f1_b))
            pre, rec, f1 = pre_b, rec_b, f1_b
        
        return pre, rec, f1
    
    def compute_acc(self, model_name, sentences):
        correct_labels = [sentences[idx][self.label_keys[model_name]] for idx in range(len(sentences))]
        pred_labels = self.predict_labels(self.models[model_name], sentences) 
        
        num_labels = 0
        num_corr_labels = 0
        for sentenceId in range(len(correct_labels)):
            for tokenId in range(len(correct_labels[sentenceId])):
                num_labels += 1
                if correct_labels[sentenceId][tokenId] == pred_labels[sentenceId][tokenId]:
                    num_corr_labels += 1

  
        return num_corr_labels/float(num_labels)
    
    def pad_characters(self, sentences):
        """ Pads the character representations of the words to the longest word in the dataset """
        # Find the longest word in the dataset
        max_char_len = self.params['max_char_length']
        if max_char_len <= 0:
            for sentence in sentences:
                for token in sentence['characters']:
                    max_char_len = max(max_char_len, len(token))
          

        for sentence_idx in range(len(sentences)):
            for token_idx in range(len(sentences[sentence_idx]['characters'])):
                token = sentences[sentence_idx]['characters'][token_idx]

                if len(token) < max_char_len:  # Token shorter than max_char_len -> pad token
                    sentences[sentence_idx]['characters'][token_idx] = np.pad(token, (0, max_char_len-len(token)), 'constant')
                else:  # Token longer than max_char_len -> truncate token
                    sentences[sentence_idx]['characters'][token_idx] = token[0:max_char_len]
    
        self.max_char_len = max_char_len
        
    def add_task_identifier(self):
        """ Adds an identifier to every token, which identifies the task the token stems from """
        taskID = 0
        for model_name in self.model_names:
            dataset = self.data[model_name]
            for dataName in ['train_matrix', 'dev_matrix', 'test_matrix']:            
                for sentence_idx in range(len(dataset[dataName])):
                    dataset[dataName][sentence_idx]['taskID'] = [taskID] * len(dataset[dataName][sentence_idx]['tokens'])
            
            taskID += 1

    def save_model(self, model_name, epoch, dev_score, test_score):
        import json
        import h5py

        if self.model_save_path == None:
            raise ValueError('model_save_path not specified.')

        save_path = self.model_save_path.replace("[DevScore]", "%.4f" % dev_score).replace("[TestScore]", "%.4f" % test_score).replace("[Epoch]", str(epoch+1)).replace("[model_name]", model_name)
        directory = os.path.dirname(save_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if os.path.isfile(save_path):
            logging.info("Model "+save_path+" already exists. Model will be overwritten")

        self.models[model_name].save(save_path, True)

        with h5py.File(save_path, 'a') as h5file:
            h5file.attrs['mappings'] = json.dumps(self.mappings)
            h5file.attrs['params'] = json.dumps(self.params)
            h5file.attrs['model_name'] = model_name
            h5file.attrs['label_key'] = self.datasets[model_name]['label']

    @staticmethod
    def load_model(model_path):
        import h5py
        import json
        from .keraslayers.ChainCRF import create_custom_objects

        model = keras.models.load_model(model_path, custom_objects=create_custom_objects())

        with h5py.File(model_path, 'r') as f:
            mappings = json.loads(f.attrs['mappings'])
            params = json.loads(f.attrs['params'])
            model_name = f.attrs['model_name']
            label_key = f.attrs['label_key']

        bilstm = BiLSTM(params)
        bilstm.set_mappings(mappings, None)
        bilstm.models = {model_name: model}
        bilstm.label_keys = {model_name: label_key}
        bilstm.idx2labels = {}
        bilstm.idx2labels[model_name] = {v: k for k, v in bilstm.mappings[label_key].items()}
        return bilstm