## Exploring the Potential of Llama Models in Automated Code Refinement: A Replication Study

Our work investigates the code refinement capabilities of two open-source models, offering practical solutions to the challenges of using LLMs in real-world software. It is an extension of the paper by Guo et al in "Exploring the Potential of ChatGPT in Automated Code Refinement: An Empirical Study".
Their replication package and extra information is available at: https://sites.google.com/view/chatgptcodereview/overview?authuser=0

### Methodology of our study - Overview
#### RQ1:
Split CodeReview and CodeReview-New into train/validation/test sets using the same partition method as the authors did: 85%, 7.5%, 7.5%.

** Note that the prompts were modified for Llama2/CodeLlama:
Added: “In your response, put the revised code between triple backticks and avoid mentioning the programming language between the backticks.” at the end of each prompt, otherwise the format of the output was unpredictable.

Put the prompt between [INST] and [/INST] tags as recommended by model documentation (reference DeepLearning.AI training on Llama2 prompt engineering: [Prompt Engineering with Llama 2 - DeepLearning.AI](https://www.deeplearning.ai/short-courses/prompt-engineering-with-llama-2/)).

1) Create 3 models for Llama 2 and 3 models for Code Llama using a temperature for each: 0.0, 0.5, 1.0. The models can be created using Ollama via a Modelfile (see example in the Google Drive)
Randomly select 125 data points from the CodeReview test dataset.
Run each model on the data points, with the 5 different prompts. Use the scripts in the replication package (modify if required) as they also automatically record the scores (bleu, EM, etc.).
Each setting is repeated 5 times to account for the randomness of predictions. The average of the 5 runs is used as the final result.
Note the results and select the best performing temperature. Note observations. Evaluate the consistency of responses of temperature 0 with the best prompt (as they do in the paper). Note which prompts obtain the best results. Compare with the results of the paper. 

2) Assess variability.
- Randomly select 250 data points from the CodeReview training/validation dataset.
- Repeat experiment 1 twice.
- Compare with the results obtained in 1 and in the paper with ChatGPT.
- Assess variability.

#### RQ2:
Run the best model with the best prompt and temperature settings on the following datasets:
- Test set of codereview
- Test set of codereview-new

Repeat the experiment 2 times
Assess variability (should not be any, if consistent with previous results at temperature 0)

#### RQ3:
Using the categorization done in the replication paper, evaluate our model’s performance based on those categories. We have 200 instances run in RQ2 from codereview-new to process. 

The categorization is done in file RQ3_RQ4_score.jsonl in the replication package.

### Content of the replication package
- Results: the generated results for RQ1 and RQ2, and additional results for Llama 3.1 for the discussion part of the paper.
- datasets: the original jsonl files from the replicated paper and the splitted versions, as well as sampling done for RQ1 and RQ2, plus the categorizations done for RQ3 from the replicated paper.
- evaluator: scoring scripts using BLEU and Exact Match metrics.
- model_versions: model cards for Llama 2 and CodeLlama
- modelfiles: the Modelfiles used to create versions of the models with each temperature
- evaluation.py: script that takes the results and runs BLEU and EM evaluators
- *rq1_rq2_llama.py*: largely inspired from the original replication package, this script contains the methods used to run RQ1 and RQ2 on Linux/Mac platforms.
- *rq1_rq2_llama_windows.py*: same as above, but with some adaptations required for Windows platform.
- *eval_codebleu_multilang.py*: get codeBLEU and codeBLEU-T metric for all models, given the results. Based on https://github.com/awsm-research/LLM-for-code-review-automatiton/blob/main/script/evaluation/eval_CodeBLEU-multi-lang.py.

#### Tested with python 3.8.0.
#### Run pip install -r requirements.txt

The scripts rq1_rq2_llama*.py are where most of the work is done. Select the best one based on your platform.

*About the models*: They were downloaded through Ollama with the commands "ollama run llama2" and "ollama run codellama". By default, the 7B, instruct versions were downloaded in their 4-bit quantized versions.
See model information here:
- Llama 2: https://ollama.com/library/llama2
- CodeLlama: https://ollama.com/library/codellama
