# -*- coding: utf-8 -*-

"""
creates or transforms the dataset e.g. sentences.txt, labels.txt
"""

import argparse
import csv
import json
import os
import re

import jieba
import numpy as np

from model.helper import Params

CHINESE_WORD_INT_PATH = "./chinese_vectors/word_idx_table.json"
STOPWORDS_PATH = "./chinese_vectors/chinese_stopwords.txt"

parser = argparse.ArgumentParser()
parser.add_argument(
    "-t", "--test", help="clean test format data", action="store_true")
parser.add_argument('--data_dir', default=None,
                    help="Directory containing the raw data to split into sentence & label txt")


def _add_sub_or_unk_word(word, vocab):
    res = []
    tmp = jieba.lcut(word, cut_all=True)
    for i in (0, -1):
        if tmp[i] in vocab:
            res.append(tmp[i])
    return res if len(res) > 0 else None
    # // return res if len(res) > 0 else "<UNK>"  # 将vocab里未出现的word替换为<UNK>


def _add_num_token(word):
    word = int(word)
    if word >= 10:
        return "<num>"  # 将数字 -> <num>
    else:
        return str(word)  # 0-9 保留


def tokenize_sentence(line, vocab):
    rule = re.compile("[^a-zA-Z0-9\u4e00-\u9fa5]")
    line = rule.sub('', line)

    sentence = []
    for word in jieba.cut(line, cut_all=False):
        if word in vocab:
            try:
                sentence.append(_add_num_token(word))
            except ValueError:
                sentence.append(word)
        else:
            sub_words = _add_sub_or_unk_word(word, vocab)
            if sub_words is not None:
                sentence += sub_words
    return sentence


def _write_rows_to_csv(lists, saved_csv_name):
    with open(saved_csv_name, 'w', newline='', encoding='utf-8', errors='ignore') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(lists)


def sentence_label_save(file_path, w2i_dict, test=False, max_len=500):

    def _string_to_int_sentence(line, lookup_table, max_len):
        int_sentence = []
        num_idx = len(lookup_table)
        if len(line) > max_len:
            line = line[:max_len]
        for word in line:
            if word == "<num>":
                int_sentence.append(num_idx)
            else:
                int_sentence.append(lookup_table[word])
        return int_sentence

    labels = []
    sentences_path = os.path.join(os.path.dirname(file_path), "sentences.csv")
    sentences_idx_path = os.path.join(
        os.path.dirname(file_path), "sentences_idx.csv")

    with open(sentences_path, 'w', newline='', encoding='utf-8', errors='ignore') as save_f:
        with open(sentences_idx_path, 'w', newline='') as save_idx_f:
            writer = csv.writer(save_f, delimiter=',')
            writer_idx = csv.writer(save_idx_f, delimiter=',')
            with open(file_path, newline='', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=',')
                next(reader)
                for idx, sentence, *label in reader:
                    sentence = tokenize_sentence(sentence, w2i_dict)
                    sentence_idx = _string_to_int_sentence(
                        sentence, w2i_dict, max_len)
                    if not test:
                        label = [int(x) for x in label]
                        labels.append(label)
                    writer.writerow(sentence)
                    writer_idx.writerow(sentence_idx)

    labels_path = os.path.join(os.path.dirname(file_path), "labels.csv")
    if not test:
        _write_rows_to_csv(labels, labels_path)


def load_chinese_table(chinese_path, stopwords_path):
    """返回去除停止词的word转int的词典

    Args:
        chinese_path (str): [description]
        stopwords_path (str): [description]

    Returns:
        (dict):
    """

    with open(chinese_path, encoding='utf-8') as f:
        word_int_table = json.load(f)

    stopwords = set()
    with open(stopwords_path, 'r', encoding='gb2312', errors='ignore') as f:
        for stopword in f:
            stopwords.add(stopword.strip())

    return {k: v for k, v in word_int_table.items() if k not in stopwords}


def main():
    args = parser.parse_args()
    if args.data_dir is None:
        raise Exception("must give a dataset folder")
    params = Params("./preprocess_params.json")
    word_int_table = load_chinese_table(CHINESE_WORD_INT_PATH, STOPWORDS_PATH)
    dataset_path = os.path.join(
        args.data_dir, os.path.basename(args.data_dir) + "_sc.csv")
    sentence_label_save(
        dataset_path, word_int_table, test=args.test)


if __name__ == "__main__":
    main()
