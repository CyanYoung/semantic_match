import pickle as pk

import numpy as np

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

from gensim.models.word2vec import Word2Vec

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from nlp_sim.util.load import load_word, load_sent


embed_dim = 200
min_freq = 3
max_vocab = 2000
seq_len = 30


def bow(sents, path_bow_model, path_bow_feature, stop_words, mode):
    if mode == 'train':
        model = CountVectorizer(stop_words=stop_words, token_pattern='\w+', min_df=min_freq)
        model.fit(sents)
        with open(path_bow_model, 'wb') as f:
            pk.dump(model, f)
    elif mode == 'dev' or mode == 'test':
        with open(path_bow_model, 'rb') as f:
            model = pk.load(f)
    else:
        raise KeyError
    sent_word_counts = model.transform(sents)  # sparse mat
    with open(path_bow_feature, 'wb') as f:
        pk.dump(sent_word_counts, f)


def tfidf(path_bow_feature, path_tfidf_model, path_tfidf_feature, mode):
    with open(path_bow_feature, 'rb') as f:
        sent_word_counts = pk.load(f)
    if mode == 'train':
        model = TfidfTransformer()
        model.fit(sent_word_counts)
        with open(path_tfidf_model, 'wb') as f:
            pk.dump(model, f)
    elif mode == 'dev' or mode == 'test':
        with open(path_tfidf_model, 'rb') as f:
            model = pk.load(f)
    else:
        raise KeyError
    sent_word_weights = model.transform(sent_word_counts)
    with open(path_tfidf_feature, 'wb') as f:
        pk.dump(sent_word_weights, f)


def word2vec(sents, path_word2vec):
    sents_split = list()
    for sent in sents:
        sents_split.append(sent.split(' '))
    model = Word2Vec(sents_split, size=embed_dim, window=3, min_count=min_freq, negative=5, iter=100)
    word_vecs = model.wv  # keyed vec
    with open(path_word2vec, 'wb') as f:
        pk.dump(word_vecs, f)
    if __name__ == '__main__':
        words = ['*', '#', '$']
        for word in words:
            print(word_vecs.most_similar(word))


def embed(sents, path_word2ind, path_word2vec, path_embed, stop_words):
    model = Tokenizer(num_words=max_vocab)
    model.fit_on_texts(sents)
    with open(path_word2ind, 'wb') as f:
        pk.dump(model, f)
    word_inds = model.word_index
    with open(path_word2vec, 'rb') as f:
        word_vecs = pk.load(f)
    vocab = word_vecs.vocab
    vocab_num = min(max_vocab, len(word_inds))
    embed_mat = np.zeros((vocab_num, embed_dim))
    for word, ind in word_inds.items():
        if word not in stop_words and word in vocab:
            if ind < max_vocab:
                embed_mat[ind] = word_vecs[word]
    with open(path_embed, 'wb') as f:
        pk.dump(embed_mat, f)


def pad(sents, path_word2ind, path_pad):
    with open(path_word2ind, 'rb') as f:
        model = pk.load(f)
    seqs = model.texts_to_sequences(sents)
    pad_mat = pad_sequences(seqs, maxlen=seq_len)
    with open(path_pad, 'wb') as f:
        pk.dump(pad_mat, f)


def vectorize(paths, mode):
    sents = load_sent(paths['data_clean'])
    stop_words = load_word(paths['stop_word'])
    bow(sents, paths['bow_model'], paths['bow_feature'], stop_words, mode)
    tfidf(paths['bow_feature'], paths['tfidf_model'], paths['tfidf_feature'], mode)
    if mode == 'train':
        word2vec(sents, paths['word2vec'])
        embed(sents, paths['word2ind'], paths['word2vec'], paths['embed'], stop_words)
    pad(sents, paths['word2ind'], paths['pad'])


if __name__ == '__main__':
    paths = dict()
    paths['data_clean'] = 'data/train_clean.csv'
    paths['stop_word'] = 'dict/stop_word.txt'
    paths['bow_model'] = 'model/vec/bow.pkl'
    paths['tfidf_model'] = 'model/vec/tfidf.pkl'
    paths['bow_feature'] = 'feature/svm/bow_train.pkl'
    paths['tfidf_feature'] = 'feature/svm/tfidf_train.pkl'
    paths['word2ind'] = 'model/vec/word2ind.pkl'
    paths['word2vec'] = 'feature/nn/word2vec.pkl'
    paths['embed'] = 'feature/nn/embed.pkl'
    paths['pad'] = 'feature/nn/pad_train.pkl'
    vectorize(paths, 'train')
    paths['data_clean'] = 'data/dev_clean.csv'
    paths['bow_feature'] = 'feature/svm/bow_dev.pkl'
    paths['tfidf_feature'] = 'feature/svm/tfidf_dev.pkl'
    paths['pad'] = 'feature/nn/pad_dev.pkl'
    vectorize(paths, 'dev')
    paths['data_clean'] = 'data/test_clean.csv'
    paths['bow_feature'] = 'feature/svm/bow_test.pkl'
    paths['tfidf_feature'] = 'feature/svm/tfidf_test.pkl'
    paths['pad'] = 'feature/nn/pad_test.pkl'
    vectorize(paths, 'test')
