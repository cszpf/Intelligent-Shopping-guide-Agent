from __future__ import print_function
import logging
"""
Computes the F1 score on BIO tagged data
"""


def compute_f1_token_basis(predictions, correct, O_Label): 

    prec = compute_precision_token_basis(predictions, correct, O_Label)
    rec = compute_precision_token_basis(correct, predictions, O_Label)
    
    f1 = 0
    if (rec+prec) > 0:
        f1 = 2.0 * prec * rec / (prec + rec)
        
    return prec, rec, f1


def compute_precision_token_basis(guessed_sentences, correct_sentences, O_Label):
    assert(len(guessed_sentences) == len(correct_sentences))
    correct_count = 0
    count = 0
    
    for sentence_idx in range(len(guessed_sentences)):
        guessed = guessed_sentences[sentence_idx]
        correct = correct_sentences[sentence_idx]
        assert(len(guessed) == len(correct))
        for idx in range(len(guessed)):
            
            if guessed[idx] != O_Label:
                count += 1
               
                if guessed[idx] == correct[idx]:
                    correct_count += 1
    
    precision = 0
    if count > 0:    
        precision = float(correct_count) / count
        
    return precision


def compute_f1(predictions, correct, idx2label, correct_bio_errors='No', encoding_scheme='BIO'):
    label_pred = []    
    for sentence in predictions:
        label_pred.append([idx2label[element] for element in sentence])
        
    label_correct = []    
    for sentence in correct:
        label_correct.append([idx2label[element] for element in sentence])
            
    encoding_scheme = encoding_scheme.upper()

    if encoding_scheme == 'IOBES':
        convert_iobes_to_bio(label_pred)
        convert_iobes_to_bio(label_correct)
    elif encoding_scheme == 'IOB':
        convert_iob_to_bio(label_pred)
        convert_iob_to_bio(label_correct)

    check_bio_encoding(label_pred, correct_bio_errors)

    prec = compute_precision(label_pred, label_correct)
    rec = compute_precision(label_correct, label_pred)

    f1 = 0
    if (rec+prec) > 0:
        f1 = 2.0 * prec * rec / (prec + rec);
        
    return prec, rec, f1


def convert_iob_to_bio(dataset):
    """ Convert inplace IOB encoding to BIO encoding """
    for sentence in dataset:
        prev_val = 'O'
        for pos in range(len(sentence)):
            first_char = sentence[pos][0]
            if first_char == 'I':
                if prev_val == 'O' or prev_val[1:] != sentence[pos][1:]:
                    sentence[pos] = 'B'+sentence[pos][1:] #Change to begin tag

            prev_val = sentence[pos]


def convert_iobes_to_bio(dataset):
    """ Convert inplace IOBES encoding to BIO encoding """    
    for sentence in dataset:
        for pos in range(len(sentence)):
            first_char = sentence[pos][0]
            if first_char == 'S':
                sentence[pos] = 'B'+sentence[pos][1:]
            elif first_char == 'E':
                sentence[pos] = 'I'+sentence[pos][1:]


def compute_precision(guessed_sentences, correct_sentences):
    assert(len(guessed_sentences) == len(correct_sentences))
    correct_count = 0
    count = 0
    
    for sentence_idx in range(len(guessed_sentences)):
        guessed = guessed_sentences[sentence_idx]
        correct = correct_sentences[sentence_idx]

        assert(len(guessed) == len(correct))
        idx = 0
        while idx < len(guessed):
            if guessed[idx][0] == 'B':  # :: A new chunk starts ::
                count += 1
                
                if guessed[idx] == correct[idx]:
                    idx += 1
                    correctly_found = True
                    
                    while idx < len(guessed) and guessed[idx][0] == 'I':  # :: Scan until it no longer starts with I ::
                        if guessed[idx] != correct[idx]:
                            correctly_found = False
                        
                        idx += 1
                    
                    if idx < len(guessed):
                        if correct[idx][0] == 'I':  # :: The chunk in correct was longer ::
                            correctly_found = False

                    if correctly_found:
                        correct_count += 1
                else:
                    idx += 1
            else:  
                idx += 1
    
    precision = 0
    if count > 0:    
        precision = float(correct_count) / count
        
    return precision


def check_bio_encoding(predictions, correct_bio_errors):
    errors = 0
    labels = 0
    
    for sentence_idx in range(len(predictions)):
        label_started = False
        label_class = None

        for labelIdx in range(len(predictions[sentence_idx])):
            label = predictions[sentence_idx][labelIdx]
            if label.startswith('B-'):
                labels += 1
                label_started = True
                label_class = label[2:]
            
            elif label == 'O':
                label_started = False
                label_class = None
            elif label.startswith('I-'):
                if not label_started or label[2:] != label_class:
                    errors += 1
                    if correct_bio_errors.upper() == 'B':
                        predictions[sentence_idx][labelIdx] = 'B-'+label[2:]
                        label_started = True
                        label_class = label[2:]
                    elif correct_bio_errors.upper() == 'O':
                        predictions[sentence_idx][labelIdx] = 'O'
                        label_started = False
                        label_class = None
            else:
                assert(False)  # :: Should never be reached ::

    if errors > 0:
        labels += errors
        logging.info("Wrong BIO-Encoding %d/%d labels, %.2f%%" % (errors, labels, errors/float(labels)*100),)


def test_encodings():
    """ Tests BIO, IOB and IOBES encoding """

    gold_bio = [['O', 'B-PER', 'I-PER', 'O', 'B-PER', 'B-PER', 'I-PER'],
               ['O', 'B-PER', 'B-LOC', 'I-LOC', 'O', 'B-PER', 'I-PER', 'I-PER'],
               ['B-LOC', 'I-LOC', 'I-LOC', 'B-PER', 'B-PER', 'I-PER', 'I-PER', 'O', 'B-LOC', 'B-PER']]

    print("--Test IOBES--")
    gold_iobes = [['O', 'B-PER', 'E-PER', 'O', 'S-PER', 'B-PER', 'E-PER'],
                 ['O', 'S-PER', 'B-LOC', 'E-LOC', 'O', 'B-PER', 'I-PER', 'E-PER'],
                 ['B-LOC', 'I-LOC', 'E-LOC', 'S-PER', 'B-PER', 'I-PER', 'E-PER', 'O', 'S-LOC', 'S-PER']]
    convert_iobes_to_bio(gold_iobes)

    for sentence_idx in range(len(gold_bio)):
        for token_idx in range(len(gold_bio[sentence_idx])):
            assert (gold_bio[sentence_idx][token_idx]==gold_iobes[sentence_idx][token_idx])

    print("--Test IOB--")
    gold_iob = [['O', 'I-PER', 'I-PER', 'O', 'I-PER', 'B-PER', 'I-PER'],
               ['O', 'I-PER', 'I-LOC', 'I-LOC', 'O', 'I-PER', 'I-PER', 'I-PER'],
               ['I-LOC', 'I-LOC', 'I-LOC', 'I-PER', 'B-PER', 'I-PER', 'I-PER', 'O', 'I-LOC', 'I-PER']]
    convert_iob_to_bio(gold_iob)

    for sentence_idx in range(len(gold_bio)):
        for token_idx in range(len(gold_bio[sentence_idx])):
            assert (gold_bio[sentence_idx][token_idx]==gold_iob[sentence_idx][token_idx])

    print("test encodings completed")


def result_to_json_iob(sentence, tags):
    item = {"string": sentence, "entities": []}
    entity_name = ""
    label = None
    for char, tag in zip(sentence, tags):
        if tag[0] == "B":
            entity_name += char
            label = tag[2:]
        elif tag[0] == "I":
            entity_name += char
        else:
            if label != None:
                item['entities'].append({"word": entity_name, "type": label})
            entity_name = ""
            label = None
    if label != None:
        item['entities'].append({"word": entity_name, "type": label})

    return item


if __name__ == "__main__":
    test_encodings()