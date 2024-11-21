import asyncio
import os
from pprint import pprint
from typing import List, Dict

import aiohttp
import diskcache as dc
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper
from pydantic import Field

_ = load_dotenv(find_dotenv())

class GoogleSearchTool(BaseTool):
	cache: dc.Cache = Field(default_factory=lambda: dc.Cache(".cache/google_search_tool"))
	google: GoogleSearchAPIWrapper = Field(default_factory=lambda: GoogleSearchAPIWrapper(k=1))
	session: aiohttp.ClientSession = None  # Add this to store the session
	limiter: AsyncLimiter = None
	google_cse_id: str = None
	google_api_key: str = None
	service_url: str = "https://www.googleapis.com/customsearch/v1"
	
	def __init__(self, name: str = "google_search",
				 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",):
		super().__init__(name=name, description=description)
		self.google_api_key = os.getenv("GOOGLE_API_KEY")
		
		self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
		self.session = aiohttp.ClientSession()
		self.limiter = AsyncLimiter(max_rate=200, time_period=60)  # 每秒最多200次请求
	
	def _run(self, query: str) -> dict | str:
		result = {"title": "", "snippet": ""}
		if query in self.cache:
			cached_result = self.cache[query]
		else:
			try:
				cached_result = self.google.results(query=query, num_results=1)[-1]
				self.cache[query] = cached_result
			except Exception as e:
				print(str(e))
				return "No results found"
		result.update({k: v for k, v in cached_result.items() if k in result})
		return result
	
	async def _arun(self, query: str) -> str | list[dict]:
		try:
			result = await self.aresults(query=query, num_results=3)
		except Exception as e:
			print("_arun Exception", str(e))
			return "No results found"
		return result
	
	async def aresults(
			self,
			query: str,
			num_results: int,
	) -> List[Dict]:
		"""Run query through GoogleSearch and return metadata.

		Args:
			query: The query to search for.
			num_results: The number of results to return.

		Returns:
			A list of dictionaries with the following keys:
				snippet - The description of the result.
				title - The title of the result.
				link - The link to the result.
		"""
		metadata_results = []
		results: List = await self._agoogle_search_results(query, nums=num_results)
		if len(results) == 0:
			return [{"Result": "No good Google Search Result was found"}]
		for result in results:
			metadata_result = {
				"title": result["title"],
				"link": result["link"],
			}
			if "snippet" in result:
				metadata_result["snippet"] = result["snippet"]
			metadata_results.append(metadata_result)
		
		return metadata_results
	
	async def _agoogle_search_results(self, query: str, nums: int = 3, ) -> List[dict]:
		if query in self.cache:
			data: List = self.cache[query]
		else:
			params = {
				"q": query,
				"cx": self.google_cse_id,
				"key": self.google_api_key,
				"num": nums,
			}
			
			try:
				async with self.limiter:
					async with self.session.get(self.service_url, params=params) as response:
						response.raise_for_status()  # Raise an exception for HTTP errors
						data: Dict = await response.json()
			except aiohttp.ClientError as e:
				print(f"Failed to retrieve data: {str(e)}")
				raise e
			data = data.get("items", [])
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
	# 创建 GoogleSearchTool 实例
	tool = GoogleSearchTool()
	from datetime import datetime
	
	async def test_query(query_id):
		"""测试单次查询"""
		start_time = datetime.now()
		print(f"[{start_time}] Query-{query_id} started")
		try:
			result = await tool.arun(f"test query {query_id}")
			end_time = datetime.now()
			pprint(f"[{end_time - start_time}] Query-{query_id} Completed: {result}")
		except Exception as e:
			print(f"Query-{query_id} failed: {str(e)}")
	
	# 模拟 100 次并发调用
	num_tasks = 100
	tasks = [test_query(i) for i in range(num_tasks)]
	
	# 等待所有任务完成
	await asyncio.gather(*tasks)
	
	# 确保关闭 session
	await tool.close()

if __name__ == '__main__':
	asyncio.run(main())
