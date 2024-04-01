import json
import random
import re
import os
import csv
import subprocess
import time
from time import sleep
import pandas as pd

from evaluation import myeval


def generate_new_prompt1(old_without_minus, review):
    '''
     the simplest prompt
    '''
    prompt = "[INST]"
    prompt += "code snippet:\n"
    prompt += "{}[]".format(old_without_minus)
    prompt += "code review:"
    prompt += review
    prompt += "Please generate the revised code according to the review.\
               In your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.[/INST]"
    return prompt
def generate_new_prompt2(old_without_minus, review):
    '''
    P1 + Scenario Description.
    '''
    prompt = "[INST]"
    prompt += "As a developer, imagine you've submitted a pull request and" \
              " your team leader requests you to make a change to a piece of code." \
              " The old code being referred to in the hunk of code changes is:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "There is the code review for this code:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review. \
                 \nIn your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.[/INST]"
    return prompt
def generate_new_prompt3(old_without_minus, review):
    '''
    P1 + Detailed Requirements.
    '''
    prompt = "[INST]"
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
    prompt += "\nPlease generate the revised code. \
               \nIn your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.[/INST]"
    return prompt
def generate_new_prompt4(old_without_minus, review):
    '''
    P1 + Concise Requirements.
    '''
    prompt = "[INST]"
    prompt += "code snippet:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "code review:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review. " \
              "Please ensure that the revised code follows the original code format" \
              " and comments, unless it is explicitly required by the review. \
              \nIn your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.[/INST]"
    return prompt
def generate_new_prompt5(old_without_minus, review):
    '''
    P4 + Scenario Description.
    '''
    prompt = "[INST]"
    prompt += "As a developer, imagine you've submitted a pull request and" \
              " your team leader requests you to make a change to a piece of code." \
              " The old code being referred to in the hunk of code changes is:\n"
    prompt += "```\n{}\n```\n".format(old_without_minus)
    prompt += "There is the code review for this code:\n"
    prompt += review
    prompt += "\nPlease generate the revised code according to the review. " \
              "Please ensure that the revised code follows the original code format" \
              " and comments, unless it is explicitly required by the review.\
              \nIn your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.[/INST]"
    return prompt

def get_model_response(prompt, modelfile):
    command = ["ollama", "run", modelfile, prompt, "/set parameter num_ctx 4096"]
    # Use subprocess.PIPE for stdout and stderr
    answer = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, encoding='utf-8')

    newcode = ""
    reply = ""
    if answer.returncode == 0:
        result = re.search(r'```(.*)```', answer.stdout, re.DOTALL)
        if result:
            newcode = result.group(1)
        else:
            newcode = "no code: " + answer.stdout
        reply = answer.stdout
    else:
        newcode = "Error: " + answer.stderr
        reply = answer.stderr
    return newcode, reply


def rq1_work(prompt_id, version_id, modelfile, temperature, datas):
    new_id = 0
    for data in datas:
        _id = data['_id']
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
        modelfile = modelfile
        for i in range(3):
            # try 3 times to get a valid response
            try:
                print("Calling llama with " + prompt + " and model: " + modelfile)
                gpt_code, gpt_answer = get_model_response(prompt, modelfile)
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
        # The CSV file path
        csv_file_path = 'output.csv'
       
        # Check if the file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_file_path)
        
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', f'record_id', f'prompt_id', f'version_id', f'temperature', f'new_prompt', f'new_code', f'new_answer',
                          f'new_em', f'new_em_trim', f'new_bleu', 
                          f'new_bleu_trim', 'old', 'new', 'review']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:  # Only write headers if file does not exist
                writer.writeheader()
            
            writer.writerow({
                'id': new_id, 
                f'record_id':_id,
                f'prompt_id':prompt_id,
                f'version_id':version_id,
                f'temperature':temperature,
                f'new_prompt': prompt,
                f'new_code': gpt_code,
                f'new_answer': gpt_answer,
                f'new_em': gpt_em,
                f'new_em_trim': gpt_em_trim,
                f'new_bleu': gpt_bleu,
                f'new_bleu_trim': gpt_bleu_trim,
                'old': old, 'new': new, 'review': review
            })
            
        print("Data saved to CSV file.")
        
        time.sleep(2)
        
        new_id += 1  # Increment ID for the next entry
        
def extract_records(read_path, start_line=0, num_records=100):
    datas = []
    with open(read_path, 'r', encoding='utf-8') as f:
        # Skip to the starting line if start_line > 0
        for _ in range(start_line):
            next(f, None)
        
        # Read the specified number of lines (num_records) starting from start_line
        for _ in range(num_records):
            try:
                line = next(f)  # Get next line from file
                data = json.loads(line)  # Convert JSON line to dictionary
                datas.append(data)
            except StopIteration:  # If there are no more lines, stop reading
                break

    return datas
    
def fetch_records_from_jsonl(jsonl_path, record_ids):
    """
    Fetch records from a .jsonl file based on a list of record_ids.
    """
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as file:
        for line in file:
            record = json.loads(line.strip())
            # Assuming '_id' is the field in the JSONL file that corresponds to 'record_id' in your CSV
            if record['_id'] in record_ids:
                records.append(record)
    return records

def call_rq1_work_with_file_data(csv_path, jsonl_path):
    """
    Reads a CSV file with record_id, prompt_id, and temperature,
    fetches corresponding records from a JSONL file,
    and calls rq1_work for each record with version_id from 1 to 4.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Correct temperature format by removing '.0' for whole numbers
    df['temperature'] = df['temperature'].apply(lambda x: str(int(x)) if x in [0.0, 1.0] else str(x))
    
    # Extract unique record_ids from the DataFrame
    unique_record_ids = df['record_id'].unique().tolist()
    
    # Fetch corresponding records from the JSONL file
    records = fetch_records_from_jsonl(jsonl_path, unique_record_ids)
    
    # Map of record_id to record for faster lookup
    record_map = {_record['_id']: _record for _record in records}
    
    version_ids = [1, 2]
    
    for index, row in df.iterrows():
        record_id = row['record_id']
        prompt_id = row['prompt_id']
        temperature = row['temperature']
        
        # Retrieve the full record from the map
        current_record = record_map.get(record_id)
        
        if current_record:
            for version_id in version_ids:
                modelfile = "llama2-" + str(temperature)
                print(f"Calling with: {modelfile}")
                print(f"Current id: {record_id}")
                
                # Call rq1_work with the current record
                rq1_work(prompt_id, version_id, modelfile, temperature, [current_record])
        else:
            print(f"Record ID {record_id} not found in JSONL file.")
        
        time.sleep(2)
            
def rq1():
    """
    Here, I have only written the logic code.
    During actual execution, multiprocessing will be used to accelerate the process.
    """
    read_path = "sampled_trainval_500.jsonl"
    
    # TODO: extract your own piece of data instead
    datas = extract_records(read_path, 0, 250)
    
    batch_size = 250
    pause_duration = 5
    
    for start_index in range(0, len(datas), batch_size):
        end_index = min(start_index + batch_size, len(datas))
        current_batch = datas[start_index:end_index]
        
        for prompt_id in range(5):
            for version_id in range(2):
                for temperature in [0,0.5,1]:
                    modelfile = "llama2-" + str(temperature)
                    print("Calling with: " + modelfile)
                    rq1_work(prompt_id, version_id, modelfile, temperature, current_batch)
                    
            if (end_index < len(datas)):
                print(f"Pausing for {pause_duration}, seconds")
                time.sleep(pause_duration)


def rq2():

    # The steps for codereview.jsonl and codereview_new.jsonl are essentially the same,

    # with the only difference being the method of storing data in the database.

    # read_path = "codereview.jsonl"

    read_path = "sampled_codereview-new_test.jsonl"
    with open(read_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_id = 0

    for line in lines:
        data = json.loads(line)
        _id = data['_id']
        old = data['old']
        new = data['new']
        review = data['review']
        old_without_minus = []

        for line in old.split("\n"):
        old_without_minus.append(line[1:])
        old_without_minus = "\n".join(old_without_minus)
        prompt = generate_new_prompt5(old_without_minus, review)
        gpt_code = "no code"
        gpt_answer = "no answer"
        modelfile = "codellama-temp0"

        print("Current id: " + str(data['_id']))

        for i in range(2):
            # try 3 times to get a valid response
            try:
                gpt_code, gpt_answer = get_model_response(prompt, modelfile)
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

        # The CSV file path
        csv_file_path = 'output_rq2.csv'

        # Check if the file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_file_path)        

        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', f'record_id', f'prompt_id', f'version_id', f'temperature', f'prompt', f'new_code', f'new_answer',
                          f'new_em', f'new_em_trim', f'new_bleu', 
                          f'new_bleu_trim', 'old', 'new', 'review']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:  # Only write headers if file does not exist
            writer.writeheader()   
            writer.writerow({
                'id': new_id, 
                f'record_id':_id,
                f'prompt_id':5,
                f'version_id':i,
                f'temperature':0,
                f'prompt': prompt,
                f'new_code': gpt_code,
                f'new_answer': gpt_answer,
                f'new_em': gpt_em,
                f'new_em_trim': gpt_em_trim,
                f'new_bleu': gpt_bleu,
                f'new_bleu_trim': gpt_bleu_trim,
                'old': old, 'new': new, 'review': review
            })
        print("Data saved to CSV file.")
        time.sleep(2)
        new_id += 1  # Increment ID for the next entry

def split_and_save():
    read_path = "codereview.jsonl"
    train_sample_path = "sampled_codereview_train.jsonl"
    validation_sample_path = "sampled_codereview_validation.jsonl"
    test_sample_path = "sampled_codereview_test.jsonl"
    
    # Read lines from the source file
    with open(read_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Set the random seed for reproducibility
    random.seed(2023)
    
    # Shuffle the indices to randomly distribute data into splits
    indices = list(range(len(lines)))
    random.shuffle(indices)
    
    # Calculate split sizes
    total_lines = len(lines)
    train_size = int(total_lines * 0.85)
    validation_size = test_size = int(total_lines * 0.075)
    
    # Split the indices for train, validation, and test
    train_indices = indices[:train_size]
    validation_indices = indices[train_size:train_size + validation_size]
    test_indices = indices[train_size + validation_size:]
    
    # Function to write a sample to a file
    def write_sample(sample_indices, path):
        with open(path, 'w', encoding='utf-8') as fw:
            for idx in sample_indices:
                fw.write(lines[idx])
    
    # Write train, validation, and test samples to their respective files
    write_sample(train_indices, train_sample_path)
    write_sample(validation_indices, validation_sample_path)
    write_sample(test_indices, test_sample_path)
    
    print(f"Train sample saved to {train_sample_path}")
    print(f"Validation sample saved to {validation_sample_path}")
    print(f"Test sample saved to {test_sample_path}")
    
def sample_test():
    read_path = "sampled_codereview_test.jsonl"
    first_sample_path = "sampled_codereview_250.jsonl"
    
    # Read lines from the source file
    with open(read_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Randomly select 500 unique indices from the total lines available
    random.seed(2023)
    # Randomly select 500 unique indices for the first sample
    first_ids = random.sample(range(len(lines)), 250)
    
    # Write the first sample to a file
    with open(first_sample_path, 'w', encoding='utf-8') as fw:
        for id in first_ids:
            fw.write(lines[id])
     
    print(f"First sample of 250 saved to {first_sample_path}")

def sample_train_val():
    train_sample_path = "sampled_codereview_train.jsonl"
    validation_sample_path = "sampled_codereview_validation.jsonl"
    combined_sample_path = "sampled_trainval_500.jsonl"
    
    # Function to read data from a file
    def read_data(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    # Read train and validation data
    train_data = read_data(train_sample_path)
    validation_data = read_data(validation_sample_path)
    
    # Combine train and validation data
    combined_data = train_data + validation_data
    
    # Set the random seed for reproducibility
    random.seed(2023)
    
    # Randomly select 500 unique items from the combined dataset
    sampled_data = random.sample(combined_data, 500)
    
    # Save the sampled data to a new file
    with open(combined_sample_path, 'w', encoding='utf-8') as fw:
        for item in sampled_data:
            fw.write(item)
    
    print(f"Combined sample of 500 saved to {combined_sample_path}")

def main():
    #split_and_save()
    #sample_train_val()
    #sample_test()
    #get_model_response("[INST] Can you write an efficient fibonacci function that works in linear time complexity?[/INST]", "codellama-temp0")
    rq1()
    #rq2()
    #call_rq1_work_with_file_data("missing-keys2-llama2.csv", "sampled_codereview_250.jsonl")

if __name__ == '__main__':
    main()
