import re

import pymongo
import pandas as pd

from evaluator.smooth_bleu import bleu_fromstr, my_bleu_fromstr
from evaluator.CodeBLEU import calc_code_bleu

def remove_comments(code):
    # 可能会删除掉#include <stdio.h> 这样的代码
    # pattern = r'(/\*.*?\*/|//.*?$|\".*?\")'
    pattern = r'/\*.*?\*/|//.*?$'
    tmp_code = re.sub(pattern, '', code, flags=re.DOTALL|re.MULTILINE)
    pattern = r'(?m)^\s*#.*?$'
    return re.sub(pattern, '', tmp_code)

def get_em_trim(gold, pred):
    gold_lines = gold.split("\n")
    pred_lines = pred.split("\n")
    jumps = [0]
    for line in pred_lines:
        jumps.append(len(line)+jumps[-1])
    gold_words = []
    pred_words = []
    for line in gold_lines:
        gold_words.extend(line.split())
    for line in pred_lines:
        pred_words.extend(line.split())
    em_trim = 0
    if len(pred_words) >= len(gold_words):
        for jump in jumps:
            if jump+len(gold_words) > len(pred_words):
                break
            if pred_words[jump:jump+len(gold_words)] == gold_words:
                em_trim = 1
                break
        # for i in range(len(pred_words)-len(gold_words)+1):
        #     if pred_words[i:i+len(gold_words)] == gold_words:
        #         em_trim = 1
        #         break
    return em_trim


def get_em_no_space(gold, pred):
    gold_lines = gold.split("\n")
    pred_lines = pred.split("\n")
    gold_line_no_space = [re.sub(r'\s', '', line) for line in gold_lines]
    pred_line_no_space = [re.sub(r'\s', '', line) for line in pred_lines]
    jumps = [0]
    for line in pred_line_no_space:
        jumps.append(len(line)+jumps[-1])
    gold_string_no_space = "".join(gold_line_no_space)
    pred_string_no_space = "".join(pred_line_no_space)
    em_no_space = 0
    if len(pred_string_no_space) >= len(gold_string_no_space):
        for jump in jumps:
            if jump+len(gold_string_no_space) > len(pred_string_no_space):
                break
            if pred_string_no_space[jump:jump+len(gold_string_no_space)] == gold_string_no_space:
                em_no_space = 1
                break
    return em_no_space


def get_em_no_comment(gold, pred):
    gold_no_comment = remove_comments(gold)
    pred_no_comment = remove_comments(pred)
    return get_em_no_space(gold_no_comment, pred_no_comment)


def get_em(gold, pred):
    gold_lines = gold.split("\n")
    pred_lines = pred.split("\n")
    gold_words = []
    pred_words = []
    for line in gold_lines:
        gold_words.extend(line.split())
    for line in pred_lines:
        pred_words.extend(line.split())
    em = 0
    if pred_words == gold_words:
        em = 1
    return em

def jaccard_similarity(linesA, linesB):
    """
    Compute the Jaccard similarity between two sets.
    """
    A = set()
    for line in linesA.split("\n"):
        A.update(line.split())
        A.update(re.findall(r'[a-zA-Z]+', line))
    B = set()
    for line in linesB.split("\n"):
        B.update(line.split())
        B.update(re.findall(r'[a-zA-Z]+', line))
    if len(A.union(B)) == 0:
        return 0
    else:
        return len(A.intersection(B)) / len(A.union(B))
def get_bleu_trim(gold, pred,bleu):
    gold_lines = gold.split("\n")
    pred_lines = pred.split("\n")
    line_num = len(pred_lines)
    gold_words = set()
    for line in gold_lines[:3]:
        gold_words.update(line.split())
    if len(gold_words) > 4:
        #用前三行的jaccard作为寻找start_line的标准
        jaccard_max = 0
        start_max = -1
        for start_line in range(max(2,line_num-len(gold_lines)+2)):
            jac = jaccard_similarity("\n".join(gold_lines[:3]), "\n".join(pred_lines[start_line:start_line+3]))
            if jac > jaccard_max:
                jaccard_max = jac
                start_max = int(start_line)
                if jaccard_max > 0.6:
                    break
        jaccard_max = 0
        end_max = line_num
        for end_line in range(line_num, start_max+len(gold_lines)-2, -1):
            jac = jaccard_similarity("\n".join(gold_lines), "\n".join(pred_lines[start_max:end_line]))
            if jac > jaccard_max:
                jaccard_max = jac
                if end_line > start_max+len(gold_lines):
                    end_max = int(end_line)
                else:
                    # 如果是预测的比较短，那么就要求jaccard更高
                    if jac > 0.8:
                        end_max = int(end_line)
        gold = "\n".join([line.strip() for line in gold_lines])
        pred = "\n".join([line.strip() for line in pred_lines[start_max:end_max]])
        bleu_trim = my_bleu_fromstr([pred], [gold], rmstop=False)[0]
    else:
        #这种实在不好定位，只能用整个jaccard作为寻找start_line、end_line的标准
        #如果bleu_trim太低，可以考虑使用整体的bleu
        jaccard_max = 0
        start_max = -1
        end_max = -1
        for start_line in range(line_num):
            for end_line in range(line_num-1, start_line, -1):
                jac = jaccard_similarity("\n".join(gold_lines), "\n".join(pred_lines[start_line:end_line]))
                if jac > jaccard_max:
                    jaccard_max = jac
                    start_max = int(start_line)
                    end_max = int(end_line)
        gold = "\n".join(gold_lines)
        pred = "\n".join(pred_lines[start_max:end_max])
        bleu_trim = my_bleu_fromstr([pred], [gold], rmstop=False)[0]
        if bleu > bleu_trim:
            bleu_trim = bleu
    return bleu_trim

def myeval(gold, pred):
    em = get_em(gold, pred)
    em_trim = get_em_trim(gold, pred)
    em_no_space = get_em_no_space(gold, pred)
    em_no_comment = get_em_no_comment(gold, pred)
    bleu = my_bleu_fromstr([pred], [gold], rmstop=False)[0]
    bleu_trim = get_bleu_trim(gold, pred, bleu)
    return em, em_trim, em_no_space, em_no_comment, bleu, bleu_trim

def get_codebleu(gold, pred, lang):
    codebleu = calc_code_bleu.get_codebleu(gold, pred, lang)
    return codebleu

def get_codebleu_trim(gold_list, pred_list, codebleu, lang):
    processed_pred_list = []
    processed_gold_list = []
    
    for gold, pred in zip(gold_list, pred_list):
        gold_lines = gold.split("\n")
        pred_lines = pred.split("\n")
        line_num = len(pred_lines)

        gold_words = set()
        for line in gold_lines[:3]:
            gold_words.update(line.split())

        if len(gold_words) > 4:
            jaccard_max = 0
            start_max = -1

            for start_line in range(max(2, line_num - len(gold_lines) + 2)):
                jac = jaccard_similarity("\n".join(gold_lines[:3]), "\n".join(pred_lines[start_line:start_line+3]))
                if jac > jaccard_max:
                    jaccard_max = jac
                    start_max = int(start_line)
                    if jaccard_max > 0.6:
                        break

            jaccard_max = 0
            end_max = line_num

            for end_line in range(line_num, start_max + len(gold_lines) - 2, -1):
                jac = jaccard_similarity("\n".join(gold_lines), "\n".join(pred_lines[start_max:end_line]))
                if jac > jaccard_max:
                    jaccard_max = jac
                    if end_line > start_max + len(gold_lines):
                        end_max = int(end_line)
                    else:
                        if jac > 0.8:
                            end_max = int(end_line)

            gold = "\n".join([line.strip() for line in gold_lines])
            pred = "\n".join([line.strip() for line in pred_lines[start_max:end_max]])
            bleu_trim = my_bleu_fromstr([pred], [gold], rmstop=False)[0]

        else:
            jaccard_max = 0
            start_max = -1
            end_max = -1

            for start_line in range(line_num):
                for end_line in range(line_num - 1, start_line, -1):
                    jac = jaccard_similarity("\n".join(gold_lines), "\n".join(pred_lines[start_line:end_line]))
                    if jac > jaccard_max:
                        jaccard_max = jac
                        start_max = int(start_line)
                        end_max = int(end_line)

            gold = "\n".join(gold_lines)
            pred = "\n".join(pred_lines[start_max:end_max])
        
        # Adjustments to pass the processed `gold` and `pred` as a list to `get_codebleu`
        processed_gold_list.append(gold)
        processed_pred_list.append(pred)

    codebleu_trim = get_codebleu(processed_gold_list, processed_pred_list, lang)

    if codebleu > codebleu_trim:
        codebleu_trim = codebleu

    return codebleu_trim