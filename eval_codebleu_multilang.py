## adapt code from https://github.com/microsoft/CodeBERT/tree/master/CodeReviewer/code/evaluator/CodeBLEU

import os, sys
import pandas as pd
import numpy as np
from evaluation import get_codebleu_trim
from evaluator.CodeBLEU.calc_code_bleu import get_codebleu

def get_output_from_df(result_path, isCsv):
    if (isCsv):
        df = pd.read_csv(result_path)

        df = df.fillna(' ')

        generated_outputs = df['new_code'].tolist()
    else:
        df = pd.read_json(result_path, lines=True)
        df = df.fillna(' ')
        generated_outputs = df['gpt_code'].tolist()

    return generated_outputs

# Process ground truth lines as done in rq1_rq2_llama.py for BLEU metric
def process_gt_lines(column):
    processed_ground_truth = []

    # remove leading + signs and leading/trailing space for each line 
    for item in column:
        lines = item.split('\n')  # Split the item into lines based on the newline character
        processed_lines = []

        for line in lines:
            print (f"Original line: {line}")
            if line.strip() != "":  # Ensure the line is not empty
                processed_lines.append(line[1:].strip())  # Remove the first character of the line
                print(f"Processed line: {line[1:].strip()}")

        # Join the processed lines back together with '\n' 
        processed_item = '\n'.join(processed_lines)
        processed_ground_truth.append(processed_item)

    return processed_ground_truth

def get_gt_from_file(result_path, isCsv):
    if (isCsv):
        df = pd.read_csv(result_path)

        df = df.fillna(' ')

        ground_truth = process_gt_lines(df['new'])
    else:
        df = pd.read_json(result_path, lines=True)
        df = df.fillna(' ')
        ground_truth = process_gt_lines(df['new'])

    return ground_truth

def get_languages_from_file(result_path):
    df = pd.read_csv(result_path)

    df = df.fillna(' ')

    languages = df['language'].tolist()

    return languages

def get_output_from_text_file(result_path):
    with open(result_path) as f:
        generated_outputs = f.readlines()

    generated_outputs = [l.strip() for l in generated_outputs]

    return generated_outputs

def get_output_from_file(result_path, isCsv):
    file_ext = result_path.split('.')[-1]

    if file_ext == 'txt':
        print('get output from text file')
        return get_output_from_text_file(result_path)
    elif file_ext == 'csv':
        print('get output from csv file')
        return get_output_from_df(result_path, True)
    elif file_ext == 'jsonl':
        print('get output from jsonl')
        return get_output_from_df(result_path, False)
    else:
        print('incorrect file extension')
        exit()


lang_dict = {'go': 'go',
    'php': 'php',
    '.cs': 'c_sharp',
    'csharp': 'c_sharp',
    'java': 'java',
    'js': 'javascript',
    'javascript': 'javascript',
    'c': 'c',
    'cpp': 'cpp',
    'rb': 'ruby',
    'ruby':'ruby',
    'py': 'python',
    'python': 'python',
    'perl': 'perl',
    'scala': 'scala',
    'objective-c':'objc',
    'sql':'sql',
    'kotlin':'kotlin',
    'swift':'swift',
    'r':'r'}

#ChatGPT, CR
#gt_file_path = 'datasets/RQ2/sampled_codereview_test.jsonl'

#ChatGPT, CRN
#gt_file_path = 'datasets/RQ2/sampled_codereview-new_test.jsonl'

#CodeLlama, CR
#gt_file_path = 'Results/RQ2/Codellama sampled_review_test.csv'

#CodeLlama, CRN
#gt_file_path = 'Results/RQ2/output_rq2_run1_codereview-new.csv'

#Llama 3.1, CR
#gt_file_path = 'Results/Llama31/output_rq2_llama31_cr-no-system-prompt.csv'

#Llama 3.1, CRN
gt_file_path = 'Results/Llama31/output_rq2_llama31_crn-no-system-prompt.csv'

print('ground truth file path:', gt_file_path)

# change 2nd parameter to False for ChatGPT
ground_truth = get_gt_from_file(gt_file_path, True)
generated_outputs = get_output_from_file(gt_file_path, True)

# Set the language file for the dataset CR or CRN
#lang_list = get_languages_from_file("datasets/languages/languages_cr.csv")
lang_list = get_languages_from_file("datasets/languages/languages_crn.csv")

df = pd.DataFrame()
df['gt'] = ground_truth
df['output'] = generated_outputs
df['lang'] = lang_list

codebleu_by_lang = {}
codebleu_trim_by_lang = {}

# Those languages are not supported by the codeBLEU parser
unsupported_list = ['scala', 'kotlin','swift','perl','objective-c','r','sql']

for name, sub_df in df.groupby('lang'):
    lang = sub_df['lang'].tolist()[0]
    if (lang in unsupported_list):
        continue

    sub_gt = sub_df['gt']
    sub_output = sub_df['output']

    print(f"Sending {len(sub_gt)} ground truth items and {len(sub_output)} generated outputs to codeBLEU for language {lang}")
    pred_results = get_codebleu(sub_gt, sub_output, lang_dict[lang])
    codebleu_by_lang[lang] = pred_results

    trim_results = get_codebleu_trim(sub_gt, sub_output, pred_results, lang_dict[lang])
    codebleu_trim_by_lang[lang] = trim_results

print('avg codeBLEU from all lang:', round(np.mean(list(codebleu_by_lang.values()))*100,2))
print(codebleu_by_lang)

print('Average codeBLEU TRIM for all languages: ', round(np.mean(list(codebleu_trim_by_lang.values()))*100,2))
print(codebleu_trim_by_lang)