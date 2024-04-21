# Course project for SOEN691 - Software Engineering for Generative AI

## Exploring the Potential of a Large Language Model Pre-Trained on Code for Automated Code Refinement - A Replication Study

This study is a replication of the paper by Guo et al in "Exploring the Potential of ChatGPT in Automated Code Refinement: An Empirical Study".
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
