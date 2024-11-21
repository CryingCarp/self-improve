import asyncio
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
	api_key: str = Field(..., description="Google Knowledge Graph Search API key")
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(".cache/google_knowledge_graph_tool"))
	session: aiohttp.ClientSession = None  # Add this to store the session
	limiter: AsyncLimiter = None
	service_url: str = "https://kgsearch.googleapis.com/v1/entities:search"
	
	def __init__(self, api_key: str, cache_dir: str = ".cache/google_knowledge_graph_tool"):
		super().__init__(api_key=api_key)
		self.cache = dc.Cache(cache_dir)
		# Initialize the aiohttp session in the __init__ method
		self.session = aiohttp.ClientSession()
		
		self.limiter = AsyncLimiter(max_rate=60, time_period=60)  # 每秒最多200次请求
	
	def _run(self, query: str, limit: int = 3) -> str:
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
		except requests.RequestException as e:
			print(f"Failed to retrieve data: {str(e)}")
			return f"Failed to retrieve data: {str(e)}"
		
		data = response.json()
		self.cache[query] = data
		return data
	
	async def _arun(self, query: str, limit: int = 3) -> str:
		if query in self.cache:
			return self.cache[query]
		
		params = {
			"query": query,
			"limit": limit,
			"indent": "True",
			"key": self.api_key,
		}
		
		try:
			async with self.limiter:
				async with self.session.get(self.service_url, params=params) as response:
					response.raise_for_status()  # Raise an exception for HTTP errors
					data = await response.json()
		except aiohttp.ClientError as e:
			print(f"Failed to retrieve data: {str(e)}")
			return f"Failed to retrieve data: {str(e)}"
		
		self.cache[query] = data
		return data
	
	# Ensure the session is closed when the object is destroyed
	async def close(self):
		if self.session:
			await self.session.close()
	
	# Optional: handle cleanup for session on deletion
	def __del__(self):
		# Ensure the session is closed when the object is deleted
		if self.session:
			import asyncio
			asyncio.create_task(self.close())


async def main():
	tool = GoogleKnowledgeGraphTool(api_key=os.environ.get("GOOGLE_API_KEY"))
	
	# Define how many requests you want to test
	num_requests = 10
	
	import time
	# Store start time
	start_time = time.time()
	
	# Create a list of async tasks to simulate multiple concurrent requests
	tasks = []
	for i in range(num_requests):
		query = f"Python programming language {i}"  # Make each query unique by appending an index
		tasks.append(tool._arun(query=query, limit=3))
	
	# Execute the requests concurrently
	responses = await asyncio.gather(*tasks)
	
	# Calculate the total time taken
	end_time = time.time()
	total_time = end_time - start_time
	
	# Print responses (if needed)
	for idx, response in enumerate(responses):
		print(f"Response {idx + 1}: {response}")
	
	# Print total time taken and rate of requests
	print(f"\nTotal time taken for {num_requests} requests: {total_time:.2f} seconds")
	print(f"Rate of requests: {num_requests / total_time:.2f} requests per second")


if __name__ == '__main__':
	asyncio.run(main())
