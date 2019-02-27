/**
 * Load IMDB data features from a local file.
 *
 * @param {array} sequences An array of strings
 * @param {string} numWords Number of words in the vocabulary. Word indices
 *   that exceed this limit will be marked as `OOV_INDEX`.
 * @param {string} maxLen Length of each sequence. Longer sequences will be
 *   pre-truncated; shorter ones will be pre-padded.
 * @return {tf.Tensor} The dataset represented as a 2D `tf.Tensor` of shape
 *   `[]` and dtype `int32` .
 */
export const PAD_INDEX = 1;  // Index of the padding character.
export const OOV_INDEX = 0;  // Index fo the OOV character.export const PAD_INDEX = 0;  // Index of the padding character.
export const MetaDataTemplate = {'batchSize': 128,
		       'numWords': 10000,
		       'maxLen': 100,
			'embeddingSize':32,
			'epochs':5,
			'validationSplit':0.2,
			'modelSaveDir':'/dist/resources'
	}

import  {padSequences} from './sequence_utils';
import * as tf from '@tensorflow/tfjs';
import * as fs from 'fs';
import * as fetch from 'node-fetch';
import * as path from 'path';
import * as jsonfile from 'jsonfile';

function loadFeatures(sequences, maxLen) {

  let words_sequences = [];
  let whole_words = []
  for (let i=0;i<sequences.length;i++)
  {
    let words = sequences[i].split("");
    words_sequences.push(words);
  }
  const paddedSequences =
      padSequences(words_sequences, maxLen, 'pre', 'pre');
  return paddedSequences;
}

/**
  * A class for text data
  *
  * This class manages the following:
  *
  * - Convert text data(as a string) into a sequences of int.
**/
export class TextData {
  /**
   * Constructor of TextData.
   *
   * @param {string} dataIdentifier An identifier for this instance of TextData.
   * @param {array} textStrings An array of
   */
  constructor(dataIdentifier, textString, sorted=true) {
    if (!dataIdentifier) {
      throw new Error('Model identifier is not provided.');
    }

    this.dataIdentifier_ = dataIdentifier;

    this.textString_ = textString;
    if (sorted) {
      this.getSortedCharSet_();
    } else {
      this.getCharSet_();
    }
  }
  /**
   * Get data identifier.
   *
   * @returns {string} The data identifier.
   */
  dataIdentifier() {
    return this.dataIdentifier_;
  }


  /**
   * Get the size of the character set.
   *
   * @returns {number} Size of the character set, i.e., how many unique
   *   characters there are in the training text data.
   */
  charSetSize() {
    return this.charSetSize_;
  }
/**
   * Get the unique character at given index from the character set.
   *
   * @param {number} index
   * @returns {string} The unique character at `index` of the character set.
   */
  getFromCharSet(index) {
    return this.charSet_[index];
  }

  /**
   * Convert text string to integer indices.
   *
   * @param {string} text Input text.
   * @returns {number[]} Indices of the characters of `text`.
   */
  textToIndices(text) {
    const indices = [];
    for (let i = 0; i < text.length; ++i) {
      indices.push(this.charSet_.indexOf(text[i])+1);
    }
    return indices;
  }
  /**
   * Get the set of unique characters from text.
   */
  getCharSet_() {
    this.charSet_ = [];
    for (let i = 0; i < this.textLen_; ++i) {
      if (this.charSet_.indexOf(this.textString_[i]) === -1) {
        this.charSet_.push(this.textString_[i]);
      }
    }
    this.charSetSize_ = this.charSet_.length;
  }
  getSortedCharSet_() {
    this.charSet_ = [];
    var map = this.textString_.reduce(function(p, word) {
      p[word] = (p[word] || 0) + 1;
      return p;
    }, {});
    this.charSet_ = Object.keys(map).sort(function (a, b) {
      return map[a] < map[b]
    });
    this.charSet_.splice(0, 0, 'pre');
  }

  toJson() {

    return JSON.stringify({'dataIdentifier_':this.dataIdentifier_,
                           'textString_': this.textString_,
                           'charSet_': this.charSet_,
                           'charSetSize_': this.charSetSize_})
  }

    static  fromJson(jsonUrl) {
    const json = jsonfile.readFileSync(jsonUrl);

    /*this.dataIdentifier_ = data.dataIdentifier;
    this.textString_ = data.textString;
    this.charSet_ = data.charSet
    this.charSetSize_ = data.charSetSize
    return this;*/
    const textdata = Object.create(TextData.prototype);
    return Object.assign(textdata, json);
  
  }
}

/**
 * Load indent targets from a array.
 *
 * @param {array}  labels An array of Int.
 * @return {tf.Tensor} The targets as `tf.Tensor` of shape `[numExamples, num_labels]`
 *   and dtype `Int32`. It has an int values.
 */
function loadTargets(labels) {
 
  const num_labels = Math.max(...labels) + 1;  
  return tf.oneHot(tf.tensor1d(labels, 'int32'), num_labels);
}

/**
 * Load data by downloading and extracting files if necessary.
 *
 * @param {number} numWords Number of words to in the vocabulary.
 * @param {number} len Length of each sequence. Longer sequences will
 *   be pre-truncated and shorter ones will be pre-padded.
 * @return
 *   xTrain: Training data as a `tf.Tensor` of shape
 *     `[numExamples, len]` and `int32` dtype.
 *   yTrain: Targets for the training data, as a `tf.Tensor` of
 *     `[numExamples, 1]` and `int32` dtype. The values are an int.
 *   xTest: The same as `xTrain`, but for the test dataset.
 *   yTest: The same as `yTrain`, but for the test dataset.
 */
export async function loadData(numWords, len) {
  /* const trainCsv = tf.data.csv(
  	'indent_train.csv', {
  		hasHeader: true,
		columnConfigs: {
  			labels: {
  				islabel: true
  			}
  		}
  	});

  const testCsv = tf.data.csv(
  
	  'indent_test.csv', {
  		hasHeader: true,
  		columnConfigs: {
  			labels: {
  				islabel: true
  			}
  		}
  	});
  */
  const csv = require('csvtojson');
  const trainJson = await csv({checkType:true}).fromFile('indent_train.csv').then((jsonObj)=>{return jsonObj});
  const testJson = await csv({checkType:true}).fromFile('indent_test.csv').then((jsonObj)=>{return jsonObj}); 

  const train_sequences = [];
  const train_labels = [];
  const test_sequences = [];
  const test_labels = [];
  trainJson.forEach(function(element){
  	train_sequences.push(element['sequence']);
  	train_labels.push(element['label']);
  });
  testJson.forEach(function(element){
        test_sequences.push(element['sequence']);
        test_labels.push(element['label']);
  });
  const xTrainChar = loadFeatures(train_sequences, len);
  const xTestChar = loadFeatures(test_sequences, len);
  const yTrain = loadTargets(train_labels);
  const yTest = loadTargets(test_labels);

  // char2number
  let whole_words = []
  for(let i=0; i < xTrainChar.length; ++i){
    whole_words = whole_words.concat(xTrainChar[i])
  }
  let charConverter = new TextData('trainTable', whole_words, true)
  const xTrainArray = []
  const xTestArray = []
  for(let i=0; i < xTrainChar.length; ++i){
    xTrainArray.push(charConverter.textToIndices(xTrainChar[i]))
  }
  for(let i=0; i < xTestChar.length; ++i){
    xTestArray.push(charConverter.textToIndices(xTestChar[i]))
  }
  let xTrain = tf.tensor2d(xTrainArray, [xTrainArray.length, len], 'int32');
  let xTest = tf.tensor2d(xTestArray, [xTestArray.length, len], 'int32');
  //save TextData
  let TextDataSerialize = charConverter.toJson();
  fs.writeFile('TextData.json', TextDataSerialize, (err)=>{
  	if (err) throw err;
  	console.log('文件已保存')})

  tf.util.assert(
      xTrain.shape[0] === yTrain.shape[0],
      'Mismatch in number of examples between xTrain and yTrain');
  tf.util.assert(
      xTest.shape[0] === yTest.shape[0],
      'Mismatch in number of examples between xTest and yTest');
  return {xTrain, yTrain, xTest, yTest};
}
