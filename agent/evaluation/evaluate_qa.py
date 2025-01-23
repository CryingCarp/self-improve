import json

import numpy as np

from agent.utils.qa import normalize_answer, multi_ref_score

#
# dataset_name: str = "hotpot_qa"
# dataset = load_dataset(
# 	"json",
# 	data_files="D:\Projects\self-improve\output\\ablation\gpt-4o-mini-2024-07-18\hotpot_qa\self-improve\without_fusion_cot_num_samples_1000_top_p_0.95_temperature_0_seed_42.jsonl",
#     split="train",)

dataset = []
with open(
		"/output/inference/gpt-3.5-turbo/hotpot_qa/self-improve/with_question_before_fusion_cot_num_samples_1000_top_p_0.95_temperature_0_seed_42.jsonl", "r") as f:
	for line in f:
		dataset.append(json.loads(line))

	
def evaluation(dataset):
	em_score = []
	f1_score = []
	precision_score = []
	recall_score = []
	error_index_list = []
	for idx, example in enumerate(dataset[:1000]):
		# assert isinstance(example['prediction'], str), "Prediction must be str"
		# print(example["answer"], example["prediction"])
		if isinstance(example["answer"], str):
			answers = [example["answer"]]
		else:
			answers = example["answer"]
		
		normalized_answers = [normalize_answer(answer) for answer in answers]
		normalized_prediction = normalize_answer(example["prediction"])
		# normalized_prediction = normalize_answer(example["pred"][-1])

		em, f1, precision, recall = multi_ref_score(normalized_prediction, normalized_answers)
		
		em_score.append(em)
		f1_score.append(f1)
		precision_score.append(precision)
		recall_score.append(recall)
		
	return em_score, f1_score, precision_score, recall_score, error_index_list

em_score, f1_score, precision_score, recall_score, error_index_list = evaluation(dataset)
print(f"EM: {np.mean(em_score)}")
print(f"F1: {np.mean(f1_score)}")
print(f"Precision: {np.mean(precision_score)}")
print(f"Recall: {np.mean(recall_score)}")
print(len(error_index_list))


