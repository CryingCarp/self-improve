import asyncio
import json
import os

import aiohttp
import diskcache as dc
import requests
from aiolimiter import AsyncLimiter
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
	api_key: str = os.environ.get("GOOGLE_API_KEY")
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(
		"/Users/ariete/Projects/self-improve/agent/inference/.cache/google_knowledge_graph_tool"))
	limiter: AsyncLimiter = None
	service_url: str = "https://kgsearch.googleapis.com/v1/entities:search"
	
	def __init__(self,
	             cache_dir: str = "/Users/ariete/Projects/self-improve/agent/inference/.cache/google_knowledge_graph_tool"):
		super().__init__()
		self.api_key = os.environ.get("GOOGLE_API_KEY")
		self.cache = dc.Cache(cache_dir)
		self.limiter = AsyncLimiter(max_rate=2, time_period=1)  # 每秒最多200次请求
	
	def _run(self, query: str, limit: int = 3) -> list:
		"""
		Run the tool with the given query and limit.
		
		Args:
			query: The entity name to search for in the Google Knowledge Graph.
			limit: The number of results to return.
		
		Returns:
			A list of results from the Google Knowledge Graph.
		"""
		if query in self.cache:
			return self.cache[query]
		
		params = {
			"query": query,
			"limit": limit,
			"indent": True,
			"key": self.api_key,
		}
		
		try:
			response = requests.get(self.service_url, params=params)
			response.raise_for_status()  # Raise an exception for HTTP errors
			data = response.json()
		except requests.RequestException as e:
			print(f"Failed to retrieve data: {str(e)}")
			return [{"Result": "Failed to retrieve data from Google Knowledge Graph"}]
		
		data = data.get("itemListElement", [{"Result": "Failed to retrieve data from Google Knowledge Graph"}])
		self.cache[query] = data
		return data
	
	async def _arun(self, query: str, limit: int = 3) -> list:
		"""
		Async version of the run method.

		Args:
			query: The entity name to search for in the Google Knowledge Graph.
			limit: The number of results to return.

		Returns:
			A list of results from the Google Knowledge Graph.
		"""
		
		if query in self.cache:
			return self.cache[query]
		
		params = {
			"query": query,
			"limit": limit,
			"indent": "True",
			"key": self.api_key,
		}
		retries = 0
		async with self.limiter:
			while retries < 3:
				async with aiohttp.ClientSession() as session:
					try:
						async with session.get(self.service_url, params=params) as response:
							# 处理成功的请求，返回数据
							response.raise_for_status()  # 如果有其他HTTP错误（如500等），会抛出异常
							data = await response.json()
							data = data.get("itemListElement",
							                [{"Result": "Failed to retrieve data from Google Knowledge Graph"}])
							# 缓存并返回结果
							self.cache[query] = data
							return data
					
					except asyncio.TimeoutError:
						retries += 1
					except Exception as e:
						retries += 1
		print(f"Failed to retrieve data from Google Knowledge Graph: {str(e)}")
		return [{"Result": "Failed to retrieve data from Google Knowledge Graph"}]


async def async_main():
	tool = GoogleKnowledgeGraphTool()
	print(tool.name)
	print(tool.args_schema)
	result = await tool._arun("Pythage 1")


def main():
	tool = GoogleKnowledgeGraphTool()
	result = tool.run("Donald Trump", limit=3)
	print(json.dumps(result[0], indent=4))

if __name__ == '__main__':
	# asyncio.run(async_main())
	main()
