from datasets import load_dataset, DatasetDict
from langchain_core.prompts import ChatPromptTemplate
from langchain import hub
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

DATASET_NAME = [
	"hotpot_qa",
	"ambig_qa",
	"trivia_qa",
	"gsm8k",
	"tabmwp",
	"svamp",
]


def process_dataset(file_path: str) -> DatasetDict:
	# Load dataset
	dataset = load_dataset("json", data_files=file_path, split="train")
	if "tabmwp" in file_path:
		updated_dataset: DatasetDict = dataset.map(
			lambda example: {
				"context": (f"Read the following table regarding {example["table_title"]}"
							f"and then use tools to get the final answer\n{example["table"]}\n"),
				"question": example["question"],
				"answer": example["answer"]})
	elif "gsm8k" in file_path:
		updated_dataset: DatasetDict = dataset.map(
			lambda example: {
				"context": "Read the following question and then use tools to get the final answer\n",
				"question": example["question"],
				"answer": example["answer"]
			})
	elif "svamp" in file_path:
		updated_dataset: DatasetDict = dataset.map(
			lambda example: {
				"context": f"Read the following text and then use tools to get the final answer\n{example['Body']}\n",
				"question": example["Question"],
				"answer": example["Answer"]
			})
	else:
		raise ValueError("Dataset not supported")
	return updated_dataset


# Load prompt
def load_prompt(dataset_name: str) -> ChatPromptTemplate:
	dataset_prompts: dict = {
		"gsm8k": "ariete/gsm8k_9shot",
		"svamp": "ariete/svamp_7shot",
		"tabmwp": "ariete/tabmwp_4shot",
		"hotpot_qa": "ariete/hotpot_qa_6shot",
		"ambig_qa": "ariete/ambig_qa_5shot",
		"trivia_qa": "ariete/trivia_qa_5shot",
	}

	if dataset_name not in dataset_prompts:
		raise ValueError(f"Dataset {dataset_name} not supported")

	prompt: ChatPromptTemplate = hub.pull(dataset_prompts[dataset_name])
	return prompt


def load_result(file_path: str) -> DatasetDict:
	dataset = load_dataset("json", data_files=file_path, split="train")
	return dataset


def main():
	# Load dataset
	prompt = load_prompt(dataset_name="hotpot_qa")
	prompt.pretty_print()
	dataset = process_dataset(file_path="/Users/ariete/Projects/self-improve/data/tabmwp.jsonl")
	unique_values = set(dataset["ans_type"])
	print(unique_values)


if __name__ == '__main__':
	main()
