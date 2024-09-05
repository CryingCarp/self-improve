from datasets import load_dataset
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


def main():
	# Load dataset
	prompt = load_prompt(dataset_name="hotpot_qa")
	prompt.pretty_print()


if __name__ == '__main__':
	main()
