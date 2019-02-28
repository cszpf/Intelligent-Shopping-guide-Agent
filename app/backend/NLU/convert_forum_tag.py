import pandas as pd
import ast
from sklearn.utils import shuffle
import pdb

def text_convert_tag(f_name,  data):
    with open(f_name, 'w') as f:
        for i, row in data.iterrows():
            tag_text = ''
            tag = row['tag']
            text = row['text']
            if len(tag) != len(text):
                print(tag)
                print(text)
                print(len(tag))
                print(len(text))
                print(i)
            for index in range(len(tag)):
                if tag[index] == '\n':
                    continue
                else:
                    if tag[index].startswith('E'):	
                        tag_text += text[index]+' I'+tag[index][1:]+'\n'
                    elif tag[index].startswith('S'):
                        tag_text += text[index]+' B'+tag[index][1:]+'\n'
                    else:
                        tag_text += text[index]+' '+tag[index]+'\n'
            f.write(tag_text+'\n')
forum = pd.read_csv('data/forum_tag.csv', header=0)
forum['tag'] = forum['tag'].apply(lambda x: ast.literal_eval(x))

forum_number = forum.shape[0]
forum = shuffle(forum)

#train 3/5
train = forum.iloc[:int(0.6*forum_number)]
#test 1/5
test = forum.iloc[int(0.6*forum_number): int(0.8*forum_number)]
#dev 1/5
dev = forum.iloc[int(0.8*forum_number):]

text_convert_tag('data/forum.train', train)
text_convert_tag('data/forum.test', test)
text_convert_tag('data/forum.dev', dev)


