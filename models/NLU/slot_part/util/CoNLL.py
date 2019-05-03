from __future__ import print_function
import os


def conll_write(output_path, sentences, headers):
    """
    Writes a sentences array/hashmap to a CoNLL format
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    fOut = open(output_path, 'w')
    
    
    for sentence in sentences:
        fOut.write("#")
        fOut.write("\t".join(headers))
        fOut.write("\n")
        for token_idx in range(len(sentence[headers[0]])):
            aceData = [sentence[key][token_idx] for key in headers]
            fOut.write("\t".join(aceData))
            fOut.write("\n")
        fOut.write("\n")
        
        
def read_conll(input_path, cols, comment_symbol=None, val_transformation=None):
    """
    Reads in a CoNLL file
    """
    sentences = []
    
    sentence_template = {name: [] for name in cols.values()}
    
    sentence = {name: [] for name in sentence_template.keys()}
    
    new_data = False
    
    for line in open(input_path, encoding='utf-8'):
        line = line.strip()
        if len(line) == 0 or (comment_symbol != None and line.startswith(comment_symbol)):
            if new_data:
                sentences.append(sentence)
                    
                sentence = {name: [] for name in sentence_template.keys()}
                new_data = False
            continue
        
        splits = line.split()
        for colIdx, colName in cols.items():
            val = splits[colIdx]
            if val_transformation != None:
                val = val_transformation(colName, val, splits)
            sentence[colName].append(val)  

        new_data = True
        
    if new_data:
        sentences.append(sentence)
            
    for name in cols.values():
        if name.endswith('_BIO'):
            iobes_name = name[0:-4]+'_class'
            
            # :: Add class ::
            class_name = name[0:-4]+'_class'
            for sentence in sentences:
                sentence[class_name] = []
                for val in sentence[name]:
                    valClass = val[2:] if val != 'O' else 'O'
                    sentence[class_name].append(valClass)
                    
            # :: Add IOB encoding ::
            iob_name = name[0:-4]+'_IOB'
            for sentence in sentences:
                sentence[iob_name] = []
                old_val = 'O'
                for val in sentence[name]:
                    new_val = val
                    
                    if new_val[0] == 'B':
                        if old_val != 'I'+new_val[1:]:
                            new_val = 'I'+new_val[1:]

                    sentence[iob_name].append(new_val)
                    old_val = new_val
                    
            # :: Add IOBES encoding ::
            iobes_name = name[0:-4]+'_IOBES'
            for sentence in sentences:
                sentence[iobes_name] = []
                
                for pos in range(len(sentence[name])):                    
                    val = sentence[name][pos]
                    next_val = sentence[name][pos+1] if (pos+1) < len(sentence[name]) else 'O'

                    new_val = val
                    if val[0] == 'B':
                        if next_val[0] != 'I':
                            new_val = 'S'+val[1:]
                    elif val[0] == 'I':
                        if next_val[0] != 'I':
                            new_val = 'E'+val[1:]

                    sentence[iobes_name].append(new_val)
                   
    return sentences