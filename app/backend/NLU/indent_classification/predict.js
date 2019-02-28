import {MetaDataTemplate} from './data';

class queryClassifier{
	constructor(MetaDir){

	this.metaData = loaidMetadata;
	this.textData = loadTextData;
	this.model = loadModel;
	}
	/*
	 * Read the local MetaData to restore the classifier
	 * 
	 * @returns {dict}
	 * */

	loadMetaData(){
	}

	/*
	 * Read the local TextData, a util used to transform char into inddex
	 * 
	 * @returns {TextData}
	 * */

	loadTextData(){
	}

	/*
	 * Read the local classifier
	 * 
	 * @returns {model}
	 * */

	loadModel(){
	}


	/*
	 *Predict the label of text
	 * 
	 * @param {string} test Input text.
	 * @retruns {Int}  label of the text
	 * */

	predict(text){
	}
}
