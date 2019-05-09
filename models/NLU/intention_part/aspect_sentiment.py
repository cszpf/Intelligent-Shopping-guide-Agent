import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import sys
import os

sys.path.append(os.path.dirname(__file__))

from attention import Attention
from index_to_word import index_word
import jieba


class Model(nn.Module):
    def __init__(self, word_size, padding_idx, embedding_size=300, embedding_params=None):
        super(Model, self).__init__()
        dropout = 0.5
        if embedding_params is not None:
            self.task_emb_1 = nn.Embedding.from_pretrained(embedding_params, freeze=False, padding_idx=padding_idx)
            self.task_emb_2 = nn.Embedding.from_pretrained(embedding_params, freeze=False, padding_idx=padding_idx)
        else:
            self.task_emb_1 = nn.Embedding(word_size, embedding_size, padding_idx=padding_idx)
            self.task_emb_2 = nn.Embedding(word_size, embedding_size, padding_idx=padding_idx)
        self.common_emb = nn.Embedding(word_size, embedding_size, padding_idx=padding_idx)
        self.emb_dropout = nn.Dropout(dropout)
        self.aspect_linear = nn.Linear(embedding_size, embedding_size * 2)

        self.bi_gru = nn.GRU(input_size=embedding_size * 2, hidden_size=embedding_size,
                             bidirectional=True, batch_first=True)
        self.gru_dropout = nn.Dropout(dropout)
        self.task_output_1 = nn.Sequential(
            nn.Linear(embedding_size * 2, 2),
            nn.LogSoftmax(dim=-1)
        )

        self.attention = Attention(embedding_size * 2)
        self.attn_dropout = nn.Dropout(dropout)
        self.task_output_2 = nn.Sequential(
            nn.Linear(embedding_size * 2, embedding_size * 2),
            nn.ReLU(),
            nn.Linear(embedding_size * 2, 3),
            nn.LogSoftmax(dim=-1)
        )

    def forward(self, x, task, mask=None):
        '''

        :param x: shape (batch_size, len)
        :param task:1 or 2
        :return:
        y: shape (batch_size, target_size)
        '''
        if task == 1:
            task_emb = self.task_emb_1(x)
            common_emb = self.common_emb(x)
            inp = torch.cat([task_emb, common_emb], dim=-1)
            inp = self.emb_dropout(inp)
            # inp:(batch, len, embedding_size*2)
            output, hidden = self.bi_gru(inp, None)
            # output:batch,len,emb_size*2
            # hidden:2,len,emb_size
            output = output.transpose(1, 2)
            # output: batch,emb_size*2,len
            output = F.max_pool1d(output, output.shape[-1]).squeeze(-1)
            output = self.gru_dropout(output)
            # output:batch,emb_size*2
            res = self.task_output_1(output)
            return res
        else:
            x, aspect = x
            if mask:
                sent_mask, aspect_mask = mask
            # x:batch_size,len
            # aspect:batch_size,aspect_len
            task_emb = self.task_emb_2(x)
            common_emb = self.common_emb(x)
            inp = torch.cat([task_emb, common_emb], dim=-1)
            inp = self.emb_dropout(inp)
            # inp:(batch, len, embedding_size*2)
            output, hidden = self.bi_gru(inp, None)
            output = self.gru_dropout(output)
            # output:batch,len,emb_size*2
            # hidden:2,len,emb_size
            aspect = self.task_emb_2(aspect)
            aspect = torch.sum(aspect, dim=1) / aspect_mask.sum(dim=1).view(-1, 1).float()
            # aspect:batch,emb_size
            aspect = self.aspect_linear(aspect)
            aspect = aspect.unsqueeze(1)
            # aspect:batch,1,emb_size*2
            attn, weights = self.attention(aspect, output, sent_mask)
            attn = self.attn_dropout(attn)
            # attn: (batch_size, 1, emb_size*2)
            attn = attn.squeeze(1)
            res = self.task_output_2(attn)

            return res


def get_model():
    path = os.path.dirname(__file__)
    word_dict = index_word()
    word_dict.load(path + '/model/word_dict.model')
    label_dict = index_word()
    label_dict.addSentence(['positive', 'no_mention', 'negative'])

    model = Model(word_size=word_dict.word_count, padding_idx=word_dict.word_to_index['<pad>'],
                  embedding_size=300, embedding_params=None)
    model.load_state_dict(torch.load(path + '/model/multitask.model'))

    def tokenizor(s):
        s = jieba.lcut(s)
        res = []
        for word in s:
            if word not in word_dict.word_to_index:
                res.extend(list(word))
            else:
                res.append(word)
        return s

    def predict(sentence, aspect):
        sentence = tokenizor(sentence)
        sentence = [word_dict.wordToIndex(word) for word in sentence]
        sentence = torch.tensor(sentence).view(1, -1)
        sent_mask = sentence == word_dict.wordToIndex('<pad>')

        aspect = tokenizor(aspect)
        aspect = [word_dict.wordToIndex(word) for word in aspect]
        aspect = torch.tensor(aspect).view(1, -1)
        aspect_mask = aspect != word_dict.wordToIndex('<pad>')

        model.eval()
        output = model((sentence, aspect), task=2, mask=(sent_mask, aspect_mask))
        output = torch.argmax(output, dim=1).item()
        label = label_dict.indexToWord(output)
        return label

    return {
        'model': model,
        'predict': predict
    }


if __name__ == '__main__':
    model = get_model()
    res = model['predict']('一般就是办公用', '办公')
    print(res)
