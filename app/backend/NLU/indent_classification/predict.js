import {TextData} from './data';
import * as tf from '@tensorflow/tfjs';
import {padSequences} from './sequence_utils';
import * as path from 'path';
import * as jsonfile from 'jsonfile';

global.fetch = require('node-fetch');
//const fetch = require("node-fetch");
const express = require('express');
export const TYPEMAP = ['COMPUTER','CAMER', 'PHONE'];

export class queryClassifier{
	constructor(){}
	async init(metaUrl, textDataJsonUrl){
	this.metaData = this.loadMetaData(metaUrl);
	this.textData = this.loadTextData(textDataJsonUrl);
	//console.log(metaUrl, textDataJsonUrl);	
	const modelUrl = this.metaData.modelSaveDir + '/model.json';
        await this.loadModel(modelUrl);
	console.log('has loaded model');
//	console.log(this.model);
	}

	/*
	 * Read the local MetaData to restore the classifier
	 * 
	 * @returns {dict}
	 * */

	 loadMetaData(metaUrl){
		try{
		 	const metadata = jsonfile.readFileSync(metaUrl);
		        //console.log(metadata.modelSaveDir);
			return metadata;

		} catch(err){
			console.log(err)
		}
	}

	/*
	 * Read the local TextData, a util used to transform char into inddex
	 * 
	 * @returns {TextData}
	 * */

	loadTextData(textDataJsonUrl){
		const textData = TextData.fromJson(textDataJsonUrl);
		
		return textData;

	}

	/*
	 * Read the local classifier
	 * 
	 * @returns {model}
	 * */

	 async loadModel(url){
		this.model = await tf.loadLayersModel('http://127.0.0.1:8081'+url);
//		console.log(this.model)
		 
	}


	/*
	 *Predict the label of text
	 * 
	 * @param {string} text Input text.
	 * @retruns {Int}  label of the text {"笔记本": 0, "相机": 1, "手机":2}
	 * */

	async predict(text){
		console.log(text);
		const paddedSequence = padSequences([text.split("")], this.metaData.maxLen);
		const indices = this.textData.textToIndices(paddedSequence[0]);
		//console.log(indices);
		
		const input = tf.tensor2d(indices, [1, this.metaData.maxLen]);
		const predictOut = this.model.predict(input);
		const predictLabel = TYPEMAP[predictOut.argMax(1).dataSync()[0]];
		console.log(predictLabel)
		return predictLabel;
	}
}

async function main(){
	var app = express();
	app.use(express.static('./'));
	var server = app.listen(8081);
	
	const classifier= new queryClassifier();
	await classifier.init('./dist/resources/metadata.json', 
			      './TextData.json');
	
	/*app.get('/' ,function(req, res){
		res.send('根目录');
	})*/

	app.get('/', async function(req, res){
        	var data = req.query.data;
		var result = await classifier.predict(data);
		res.send(result);
        })
}


main().then(console.log, console.error);
