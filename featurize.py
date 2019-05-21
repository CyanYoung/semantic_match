import pickle as pk

import numpy as np
from scipy.sparse import csr_matrix

from sklearn.feature_extraction.text import CountVectorizer

from util import flat_read


min_freq = 5

path_bow = 'model/ml/bow.pkl'


def bow(sents, path_bow, mode):
    if mode == 'train':
        model = CountVectorizer(token_pattern='\w', min_df=min_freq)
        model.fit(sents)
        with open(path_bow, 'wb') as f:
            pk.dump(model, f)
    else:
        with open(path_bow, 'rb') as f:
            model = pk.load(f)
    return model.transform(sents).toarray()


def merge(sents):
    bound = int(len(sents) / 2)
    sent1s, sent2s = sents[:bound], sents[bound:]
    diffs, prods = list(), list()
    for sent1, sent2 in zip(sent1s, sent2s):
        diffs.append(np.abs(sent1 - sent2))
        prods.append(sent1 * sent2)
    return csr_matrix(np.hstack((diffs, prods)))


def featurize(path_data, path_sent, path_label, mode):
    sent1s = flat_read(path_data, 'text1')
    sent2s = flat_read(path_data, 'text2')
    labels = flat_read(path_data, 'label')
    sents = sent1s + sent2s
    sents = bow(sents, path_bow, mode)
    sents = merge(sents)
    labels = np.array(labels)
    with open(path_sent, 'wb') as f:
        pk.dump(sents, f)
    with open(path_label, 'wb') as f:
        pk.dump(labels, f)


if __name__ == '__main__':
    path_data = 'data/train.csv'
    path_sent = 'feat/ml/sent_train.pkl'
    path_label = 'feat/label_train.pkl'
    featurize(path_data, path_sent, path_label, 'train')
    path_data = 'data/test.csv'
    path_sent = 'feat/ml/sent_test.pkl'
    path_label = 'feat/label_test.pkl'
    featurize(path_data, path_sent, path_label, 'test')
