import json
import random
import re
from time import sleep

import openai

from codee.gq.final_website.evaluation import myeval


def generate_new_prompt1(old_without_minus, review):
    '''
     the simplest prompt
    '''
    prompt = ""
    prompt += "code snippet:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "code review:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review"
    return prompt
def generate_new_prompt2(old_without_minus, review):
    '''
    P1 + Scenario Description.
    '''
    prompt = ""
    prompt += "As a developer, imagine you've submitted a pull request and" \
              " your team leader requests you to make a change to a piece of code." \
              " The old code being referred to in the hunk of code changes is:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "There is the code review for this code:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review"
    return prompt
def generate_new_prompt3(old_without_minus, review):
    '''
    P1 + Detailed Requirements.
    '''
    prompt = ""
    prompt += "You will be provided with a partial code snippet and a code review message" \
              " for the given code. Your task is to generate a revised code snippet based" \
              " on the review message and the provided code. However, you should not complete" \
              " the partial code. Your output should consist of changes, modifications," \
              " deletions or additions to the provided code snippet that address the issues" \
              " raised in the code review. Note that you are not required to write new code" \
              " from scratch, but rather revise and improve the given code.\n" \
              "Provided partial code:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "Code review:\n"
    prompt += review
    prompt += "\nPlease generate the revised code."
    return prompt
def generate_new_prompt4(old_without_minus, review):
    '''
    P1 + Concise Requirements.
    '''
    prompt = ""
    prompt += "code snippet:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "code review:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review. " \
              "Please ensure that the revised code follows the original code format" \
              " and comments, unless it is explicitly required by the review."
    return prompt
def generate_new_prompt5(old_without_minus, review):
    '''
    P4 + Scenario Description.
    '''
    prompt = ""
    prompt += "As a developer, imagine you've submitted a pull request and" \
              " your team leader requests you to make a change to a piece of code." \
              " The old code being referred to in the hunk of code changes is:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "There is the code review for this code:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review. " \
              "Please ensure that the revised code follows the original code format" \
              " and comments, unless it is explicitly required by the review."
    return prompt

def get_chatgptapi_response(prompt,temperature=1.0):
    openai.api_key = "sk-xxxx" # your api key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an experienced developer."},
            {"role": "user", "content": prompt},
        ],
        temperature = float(temperature),
     )
    # print(response)
    answer = response["choices"][0]["message"]["content"]
    # print("answer: ",answer)
    result = re.search(r'```(.*)```', answer,re.DOTALL)
    # print("result: ",result)
    if result:
        newcode = result.group(1)
    else:
        newcode = "no code"
        print("no code:")
        print(answer)
    return newcode,answer


def rq1_work(prompt_id, version_id, temperature, datas):
    new_id = 0
    for data in datas:
        old = data['old']
        new = data['new']
        review = data['review']
        old_without_minus = []
        for line in old.split("\n"):
            old_without_minus.append(line[1:])
        old_without_minus = "\n".join(old_without_minus)
        prompt1 = generate_new_prompt1(old_without_minus, review)
        prompt2 = generate_new_prompt2(old_without_minus, review)
        prompt3 = generate_new_prompt3(old_without_minus, review)
        prompt4 = generate_new_prompt4(old_without_minus, review)
        prompt5 = generate_new_prompt5(old_without_minus, review)
        prompts = [prompt1, prompt2, prompt3, prompt4, prompt5]
        prompt = prompts[int(prompt_id)]
        gpt_code = "no code"
        gpt_answer = "no answer"
        for i in range(100):
            # try 3 times to get a valid response
            try:
                gpt_code, gpt_answer = get_chatgptapi_response(prompt, temperature)
            except:
                print("error, id:{} try the {}th time".format(id, i))
                sleep(60)
                if i >= 3:
                    for j in range(360):
                        print("waiting for manual stop or {}0s".format(360 - j))
                        with open('manual_stop.json', 'r') as f:
                            data = json.load(f)
                            if data["manual_stop"]:
                                print("manual stop")
                                # pdf.save()
                                exit(0)
                        sleep(10)
                continue
            break
        save_name = "_{}_{}_{}".format(prompt_id, version_id, int(float(temperature) * 10))
        # calc the em and bleu
        new_code = []
        for line in new.split("\n"):
            if line.strip() != "":
                new_code.append(line[1:].strip())
        new_code = "\n".join(new_code)
        gpt_em, gpt_em_trim, _, _, gpt_bleu, gpt_bleu_trim \
            = myeval(new_code, gpt_code)
        # save to mongodb
        # my_dict = {"_id": new_id, "new_prompt" + save_name: prompt,
        #             "new_code" + save_name: gpt_code,
        #             "new_answer" + save_name: gpt_answer,
        #             "new_em" + save_name: gpt_em,
        #             "new_em_trim" + save_name: gpt_em_trim,
        #             "new_bleu" + save_name: gpt_bleu,
        #             "new_bleu_trim" + save_name: gpt_bleu_trim,
        #             "old": old, "new": new, "review": review}
        # col_gpt.update_one({"_id": new_id, }, {"$set": my_dict}, upsert=True)
        # print("id: ", new_id)
        # print("prompt: ", prompt)
        # print("gpt_code: ", gpt_code)
        # print("gpt_answer: ", gpt_answer)
        # print("gpt_em_trim: ", gpt_em_trim)
        # print("gpt_bleu_trim: ", gpt_bleu_trim)
        # print("====================================")
        new_id += 1


def rq1():
    """
    Here, I have only written the logic code.
    During actual execution, multiprocessing will be used to accelerate the process.
    """
    read_path = "codereview.jsonl"
    with open(read_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    #random select 500 from 10304
    random.seed(2023)
    ids = random.sample(range(10304), 500)
    datas = []
    for line in lines:
        data = json.loads(line)
        id = data['_id']
        if id in ids:
            datas.append(data)
    for prompt_id in range(5):
        for version_id in range(5):
            for temperature in [0,0.5, 1, 1.5, 2]:
                rq1_work(prompt_id, version_id, temperature, datas)


def rq2():
    # The steps for codereview.jsonl and codereview_new.jsonl are essentially the same,
    # with the only difference being the method of storing data in the database.
    # read_path = "codereview.jsonl"
    read_path = "codereview_new.jsonl"
    with open(read_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        data = json.loads(line)
        old = data['old']
        new = data['new']
        review = data['review']
        old_without_minus = []
        for line in old.split("\n"):
            old_without_minus.append(line[1:])
        old_without_minus = "\n".join(old_without_minus)
        prompt = generate_new_prompt2(old_without_minus, review)
        gpt_code = "no code"
        gpt_answer = "no answer"
        for i in range(100):
            # try 3 times to get a valid response
            try:
                gpt_code, gpt_answer = get_chatgptapi_response(prompt, temperature=0)
            except:
                print("error, id:{} try the {}th time".format(id, i))
                sleep(60)
                if i >= 3:
                    for j in range(360):
                        print("waiting for manual stop or {}0s".format(360 - j))
                        with open('manual_stop.json', 'r') as f:
                            data = json.load(f)
                            if data["manual_stop"]:
                                print("manual stop")
                                # pdf.save()
                                exit(0)
                        sleep(10)
                continue
            break
        # calc the em and bleu
        new_code = []
        for line in new.split("\n"):
            if line.strip() != "":
                new_code.append(line[1:].strip())
        new_code = "\n".join(new_code)
        gpt_em, gpt_em_trim, _, _, gpt_bleu, gpt_bleu_trim \
            = myeval(new_code, gpt_code)
        # save to db


def main():
    rq1()
    rq2()


if __name__ == '__main__':
    main()