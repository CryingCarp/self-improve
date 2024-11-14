import os

import diskcache as dc
import requests
from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import BaseTool
from pydantic import Field

_ = load_dotenv(find_dotenv())


class GoogleKnowledgeGraphTool(BaseTool):
	name: str = "google_knowledge_graph"
	description: str = (
		"This tool searches for entities in the Google Knowledge Graph. "
		"It provides information about people, places, things, and concepts. "
		"Useful when you need to get information about a specific entity. "
		"Input should be an entity name."
	)
	api_key: str = Field(..., description="Google Knowledge Graph Search API key")
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(".cache/google_knowledge_graph_tool"))
	
	def __init__(self, api_key: str, cache_dir: str = ".cache/google_knowledge_graph_tool"):
		super().__init__(api_key=api_key)
		self.cache = dc.Cache(cache_dir)
	
	async def _run(self, query: str, limit: int = 3) -> str:
		if query in self.cache:
			return self.cache[query]
		
		service_url = "https://kgsearch.googleapis.com/v1/entities:search"
		params = {
			"query": query,
			"limit": limit,
			"indent": True,
			"key": self.api_key,
		}
		
		try:
			response = requests.get(service_url, params=params)
			response.raise_for_status()  # Raise an exception for HTTP errors
		except requests.RequestException as e:
			print(f"Failed to retrieve data: {str(e)}")
			return f"Failed to retrieve data: {str(e)}"
		
		data = response.json()
		self.cache[query] = data
		return data
	
	def _arun(self, query: str, limit: int = 3) -> str:
		if query in self.cache:
			return self.cache[query]
		
		service_url = "https://kgsearch.googleapis.com/v1/entities:search"
		params = {
			"query": query,
			"limit": limit,
			"indent": True,
			"key": self.api_key,
		}
		
		try:
			response = requests.get(service_url, params=params)
			response.raise_for_status()  # Raise an exception for HTTP errors
		except requests.RequestException as e:
			print(f"Failed to retrieve data: {str(e)}")
			return f"Failed to retrieve data: {str(e)}"
		
		data = response.json()
		self.cache[query] = data
		return data
	
	def _format_results(self, data: dict) -> str:
		results = data.get("itemListElement", [])
		formatted_results = []
		
		for element in results:
			result = element.get("result", {})
			name = result.get("name", "N/A")
			score = element.get("resultScore", 0)
			formatted_results.append(f"{name} ({score})")
		
		return "\n".join(formatted_results) if formatted_results else "No results found."


def main():
	google_knowledge_graph = GoogleKnowledgeGraphTool(api_key=os.environ.get("GOOGLE_API_KEY"))
	query = "Trump"
	result = google_knowledge_graph.run(query)
	print("result", result)


if __name__ == '__main__':
	main()
