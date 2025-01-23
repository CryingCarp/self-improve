import re

# tabmwp
import numexpr
import numpy as np
from datasets import load_dataset

from agent.utils.maths import finqa_equal

# gsm8k
# dataset_name: str = "gsm8k"
# dataset = load_dataset("json",
#                        data_files="D:\Projects\self-improve\output\inference\gpt-4o-mini\gsm8k\pot\\num_samples_-1_top_p_0.95_temperature_0_seed_42.jsonl",
#                        split="train")
#
# score = []
# for idx, item in enumerate(dataset):
# 	answer = re.sub(r",", "", item["answer"])
# 	# prediction = re.sub(r",", "", item["prediction"])
# 	# if prediction == "None":
# 	# 	score.append(0)
# 	# 	print(idx, item["prediction"], item["answer"])
# 	# 	continue
# 	# else:
# 	# 	prediction = re.findall(r"[+-]\d+\.\d+|\d+\.\d+|[+-]\d+|\d+", prediction)
# 	# 	if not prediction:
# 	# 		score.append(0)
# 	# 		continue
# 	# 	else:
# 	# 		prediction = prediction[0]
# 	# 	score.append(finqa_equal(float(prediction), float(answer)))
# 	item["code"] = item["code"].replace("print(answer)", "")
# 	item["prediction"], report = execute(item["code"])
# 	if item["prediction"] is None:
# 		score.append(0)
# 		continue
# 	if item["prediction"] is str:
# 		if item["prediction"] == "None":
# 			score.append(0)
# 			continue
# 		else:
# 			prediction = re.sub(r",", "", item["prediction"])
# 			matches = re.findall(r"[+-]\d+\.\d+|\d+\.\d+|[+-]\d+|\d+", prediction)
# 			if matches:
# 				prediction = matches[0]
# 			else:
# 				score.append(0)
# 				continue
# 	else:
# 		prediction = item["prediction"]
# 	try:
# 		score.append(finqa_equal(float(prediction), float(answer)))
# 	except:
# 		print('=' * 100)
# 		print(idx, item["prediction"], item["answer"])
# 		print(item["code"])
# print(f"Accuracy: {np.mean(score)}")
# dataset_name: str = "tabmwp"
dataset = load_dataset("json",
                       data_files="D:\Projects\self-improve\output\\ablation\gpt-4o-mini-2024-07-18\\tabmwp1k\self-improve\without_critique_pot_num_samples_-1_top_p_0.95_temperature_0_seed_42.jsonl",
                       split="train")

score = []
for idx, item in enumerate(dataset):
	item["prediction"] = re.sub(r"\n", "", item["prediction"])
	if item["prediction"] is None or item["prediction"] == "None":
		print(idx, item["prediction"], item["answer"])
		score.append(0)
		continue
	# 多选
	if item['ques_type'] == "multi_choice":
		score.append(item["answer"] == item["prediction"])
	# 分数
	elif answer := re.findall(r"\d+/\d+", item["answer"]):
		prediction = re.findall(r"\d+/\d+", item["prediction"])
		if prediction:
			score.append(answer[0] == prediction[0])
			if not answer[0] == prediction[0]:
				print(idx, item["prediction"], item["answer"])
		else:
			score.append(0)
			print(idx, item["prediction"], item["answer"])
	else:
		prediction = re.sub(r",", "", item["prediction"])
		answer = re.sub(r",", "", item["answer"])
		prediction = re.findall(r"[+-]\d+\.\d+|\d+\.\d+|\d+/\d+|[+-]\d+|\d+", prediction)
		if not prediction:
			score.append(0)
			print(idx, item["prediction"], item["answer"])
			continue
		try:
			score.append(float(numexpr.evaluate(prediction[0])) == float(answer))
		except:
			print(prediction, answer)

print(f"Accuracy: {np.mean(score)}")

# SVAMP
dataset_name: str = "svamp"
dataset = load_dataset("json",
                       data_files="D:\Projects\self-improve\output\\ablation\gpt-4o-mini-2024-07-18\gsm8k\self-improve\pot_num_samples_-1_top_p_0.95_temperature_0_seed_42.jsonl",
                       split="train")

score = []
for idx, item in enumerate(dataset):
	prediction = re.sub(r",", "", item["prediction"])
	answer = re.sub(r",", "", item["answer"])
	if prediction == "None":
		score.append(0)
		print(idx, item["prediction"], item["answer"])
		continue
	else:
		prediction = re.findall(r"[+-]\d+\.\d+|\d+\.\d+|[+-]\d+|\d+", prediction)
		if not prediction:
			score.append(0)
			continue
		else:
			prediction = prediction[0]
		score.append(finqa_equal(float(prediction), float(answer)))
	try:
		score.append(finqa_equal(float(prediction), float(answer)))
	except:
		print('=' * 100)
		print(idx, item["prediction"], item["answer"])
		print(item["code"])
print(f"Accuracy: {np.mean(score)}")
