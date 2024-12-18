import json

from datasets import load_dataset, Dataset
from dotenv import load_dotenv, find_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate

_ = load_dotenv(find_dotenv())

DATASET_NAME: list[str] = [
	"hotpot_qa",
	"ambig_qa",
	"trivia_qa",
	"gsm8k",
	"tabmwp",
	"svamp",
	"toxicity",
	"gsmhard"
]


def process_dataset(dataset_name: str) -> Dataset:
	assert dataset_name is not None, "Dataset name is required"
	# data_file_path: str = f"../../data/raw_data/{dataset_name}.jsonl"
	# Load dataset
	# dataset = load_dataset("json", data_files=data_file_path)
	save_file_path = f"../../data/processed_data/{dataset_name}.jsonl"
	if dataset_name == "hotpot_qa":
		raw_dataset: Dataset = load_dataset(path='hotpot_qa', name="distractor", split='validation',
		                                    trust_remote_code=True)
		updated_dataset: Dataset = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["question"], # type: str
				"answer": [example["answer"]] # type: list[str]
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
	elif dataset_name == "ambig_qa":
		
		def process_example(sample):
			if sample['annotations']['type'][0] == "singleAnswer":
				# single answer
				answers = []
				for ans in sample['annotations']['answer']:
					answers.extend(ans)
				sample['answer'] = list(set(answers))
			else:
				# random choose a question with multiple answers
				qa_pairs = sample['annotations']['qaPairs'][0]
				# rand_i = random.randint(0, len(qa_pairs['question']) - 1)
				sample['question'] = qa_pairs['question'][0]
				sample['answer'] = qa_pairs['answer'][0]
			
			return {
				"context": "", # type: str
				"question": sample['question'], # type: str
				"answer": sample['answer'] # type: list[str]
			}
		
		raw_dataset: Dataset = load_dataset(path='ambig_qa', name="light", split='validation')
		updated_dataset: Dataset = raw_dataset.map(process_example).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
	elif dataset_name == "trivia_qa":
		raw_dataset: Dataset = load_dataset(path='trivia_qa', name="rc.nocontext", split='validation')
		updated_dataset: Dataset = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["question"], # type: str
				"answer": example["answer"]['aliases'] # type: list[str]
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
	elif dataset_name == "tabmwp1k":
		raw_dataset = load_dataset("Arietem/tabmwp", split="train")

		def process_example(example: dict) -> dict:
			if example["ques_type"] == "multi_choice":
				question = f"{example['question']} Choose from the the options: {example['choices']}"
			else:
				question = example['question']
			return {
				"context": f"Read the following table regarding \"{example['table_title']}\" and then answer a question.\n\n{example['table']}", # type: str
				"question": question, # type: str
				"answer": example["answer"], # type: str
				"ques_type": example["ques_type"], # type: str
				"choices": example["choices"] # type: list[str]
			}
		updated_dataset = raw_dataset.map(process_example).select_columns(["context", "question", "answer", "ques_type", "choices"])
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "tabmwp":
		with open("../../data/raw_data/tabmwp/tabmwp.json", "r") as file:
			data = json.load(file)
		for key in data.keys():
			if data[key]["ques_type"] == "multi_choice":
				data[key]["question"] = f"{data[key]['question']} Choose from the the options: {data[key]['choices']}"
			data[key]["question"] = (f"Read the following table regarding \"{data[key]['table_title']}\" and then answer "
			                         f"a question.\n\n{data[key]['table']}\n\n{data[key]['question']}")
		
		with open(save_file_path, 'w') as file:
			for key, value in data.items():
				file.write(json.dumps(value) + "\n")
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "gsm8k":
		raw_dataset: Dataset = load_dataset(path="gsm8k", name="main", split="test")
		updated_dataset: Dataset = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["question"], # type: str
				"answer": example["answer"].split("#### ")[-1] # type: str
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "svamp":
		raw_dataset: Dataset = load_dataset(path="svamp", split="train")
		updated_dataset: Dataset = raw_dataset.map(
			lambda example: {
				"context": example['Body'], # type: str
				"question": example["Question"], # type: str
				"answer": example["Answer"] # type: str
			})
	elif dataset_name == "toxicity":
		raw_dataset: Dataset = load_dataset(path="json", data_files="../../data/raw_data/toxicity/test.jsonl",
		                                    split="train")
		updated_dataset: Dataset = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["prompt"]["text"], # type: str
				"answer": example["continuation"]["text"] # type: str
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "gsmhard":
		raw_dataset: Dataset = load_dataset("reasoning-machines/gsm-hard", split="train")
		updated_dataset: Dataset = raw_dataset.rename_columns({'input': 'question', 'target': 'answer'})
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")

	else:
		raise ValueError("Dataset not supported")
	return updated_dataset


# Load prompt
def load_prompt(dataset_name: str, mode: str) -> ChatPromptTemplate:
	if mode in ["cot", "self-consistency"]:
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_cot",
			"gsmhard": "arietem/gsm8k_cot",
			"svamp": "arietem/svamp_cot",
			"tabmwp": "arietem/tabmwp_cot",
			"hotpot_qa": "arietem/hotpot_qa_cot",
			"ambig_qa": "arietem/ambig_qa_cot",
			"trivia_qa": "arietem/trivia_qa_cot",
			"math": "arietem/math_cot",
		}
	elif mode == "direct":
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_direct",
			"gsmhard": "arietem/gsm8k_direct",
			"svamp": "arietem/svamp_direct",
			"tabmwp": "arietem/tabmwp_direct",
			"hotpot_qa": "arietem/hotpot_qa_direct",
			"ambig_qa": "arietem/ambig_qa_direct",
			"trivia_qa": "arietem/trivia_qa_direct",
			"toxicity": "arietem/toxicity_direct",
			"math": "arietem/math_direct"
		}
	elif mode == "critic":
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_critic",
			"gsmhard": "arietem/gsm8k_critic",
			"svamp": "arietem/svamp_critic",
			"tabmwp": "arietem/tabmwp_critic",
			"hotpot_qa": "arietem/hotpot_qa_critic",
			"ambig_qa": "arietem/ambig_qa_critic",
			"trivia_qa": "arietem/trivia_qa_critic",
			"toxicity": "arietem/toxicity_critic"
		}
	elif mode == "react":
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_react",
			"gsmhard": "arietem/gsm8k_react",
			"svamp": "arietem/svamp_react",
			"tabmwp": "arietem/tabmwp_react",
			"hotpot_qa": "arietem/hotpot_qa_react",
			"ambig_qa": "arietem/ambig_qa_react",
			"trivia_qa": "arietem/trivia_qa_react",
			"toxicity": "arietem/toxicity_react"
		}
	elif mode == "pot":
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_pot",
			"gsmhard": "arietem/gsm8k_pot",
			"svamp": "arietem/svamp_pot",
			"tabmwp": "arietem/tabmwp_pot",
			"math": "arietem/math_pot",
		}
	
	if dataset_name not in dataset_prompts:
		raise ValueError(f"Dataset {dataset_name} not supported")
	
	prompt: ChatPromptTemplate = hub.pull(dataset_prompts[dataset_name])
	return prompt


def load_processed_data(dataset_name: str, file_path: str) -> Dataset:
	processed_dataset = load_dataset("json", data_files=file_path, split="train")
	return processed_dataset


def main():
	# Load dataset
	# prompt = load_prompt(dataset_name="hotpot_qa")
	# prompt.pretty_print()
	# dataset: DatasetDict = process_dataset(dataset_name="trivia_qa")
	# unique_values = set(dataset["ans_type"])
	# print(unique_values)
	# print(dataset)
	process_dataset("tabmwp")


if __name__ == '__main__':
	main()
