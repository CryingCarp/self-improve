from datasets import load_dataset, DatasetDict
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
	"toxicity"
]


def process_dataset(dataset_name: str) -> DatasetDict:
	assert dataset_name is not None, "Dataset name is required"
	# data_file_path: str = f"../../data/raw_data/{dataset_name}.jsonl"
	# Load dataset
	# dataset = load_dataset("json", data_files=data_file_path)
	save_file_path = f"../../data/processed_data/{dataset_name}.jsonl"
	if dataset_name == "hotpot_qa":
		raw_dataset: DatasetDict = load_dataset(path='hotpot_qa', name="distractor", split='validation', trust_remote_code=True)
		updated_dataset: DatasetDict = raw_dataset.map(
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
		
		raw_dataset: DatasetDict = load_dataset(path='ambig_qa', name="light", split='validation')
		updated_dataset: DatasetDict = raw_dataset.map(process_example).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
	elif dataset_name == "trivia_qa":
		raw_dataset: DatasetDict = load_dataset(path='trivia_qa', name="rc.nocontext", split='validation')
		updated_dataset: DatasetDict = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["question"], # type: str
				"answer": example["answer"]['aliases'] # type: list[str]
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
	elif dataset_name == "tabmwp":
		raw_dataset = load_dataset("Arietem/tabmwp", split="train")
		updated_dataset = raw_dataset.map(
			lambda example: {
				"context": f"Read the following table regarding {example['table_title']}\n\n{example['table']}\n", # type: str
				"question": example["question"], # type: str
				"answer": example["answer"] # type: str
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "gsm8k":
		raw_dataset: DatasetDict = load_dataset(path="gsm8k", name="main", split="test")
		updated_dataset: DatasetDict = raw_dataset.map(
			lambda example: {
				"context": "", # type: str
				"question": example["question"], # type: str
				"answer": example["answer"].split("#### ")[-1] # type: str
			}).select_columns(["context", "question", "answer"])
		updated_dataset.to_json(save_file_path)
		print(f"Saved dataset to {save_file_path}")
	elif dataset_name == "svamp":
		raw_dataset: DatasetDict = load_dataset(path="svamp")
		updated_dataset: DatasetDict = raw_dataset.map(
			lambda example: {
				"context": example['Body'], # type: str
				"question": example["Question"], # type: str
				"answer": example["Answer"] # type: str
			})
	else:
		raise ValueError("Dataset not supported")
	return updated_dataset


# Load prompt
def load_prompt(dataset_name: str, mode: str) -> ChatPromptTemplate:
	if mode == "cot":
		dataset_prompts: dict = {
			"gsm8k": "ariete/gsm8k_9shot",
			"svamp": "ariete/svamp_7shot",
			"tabmwp": "ariete/tabmwp_4shot",
			"hotpot_qa": "ariete/hotpot_qa_6shot",
			"ambig_qa": "ariete/ambig_qa_5shot",
			"trivia_qa": "ariete/trivia_qa_5shot",
		}
	else:
		dataset_prompts: dict = {
			"gsm8k": "arietem/gsm8k_direct",
			"svamp": "arietem/svamp_direct",
			"tabmwp": "arietem/tabmwp_direct",
			"hotpot_qa": "arietem/hotpot_qa_direct",
			"ambig_qa": "arietem/ambig_qa_direct",
			"trivia_qa": "arietem/trivia_qa_direct",
		}
	
	if dataset_name not in dataset_prompts:
		raise ValueError(f"Dataset {dataset_name} not supported")
	
	prompt: ChatPromptTemplate = hub.pull(dataset_prompts[dataset_name])
	return prompt


def load_processed_data(dataset_name: str) -> DatasetDict:
	processed_dataset = load_dataset("json", data_files=f"../../data/processed_data/{dataset_name}.jsonl",
									 split="train")
	return processed_dataset


def main():
	# Load dataset
	# prompt = load_prompt(dataset_name="hotpot_qa")
	# prompt.pretty_print()
	# dataset: DatasetDict = process_dataset(dataset_name="trivia_qa")
	# unique_values = set(dataset["ans_type"])
	# print(unique_values)
	# print(dataset)
	dataset = load_processed_data("hotpot_qa")
	print(dataset)


if __name__ == '__main__':
	main()
