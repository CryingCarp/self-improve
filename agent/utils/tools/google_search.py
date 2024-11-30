import asyncio
import logging
import os
import time
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
	cache: dc.Cache = Field(default_factory=lambda: dc.Cache(
		"/Users/ariete/Projects/self-improve/agent/inference/.cache/google_search_tool"))
	google: GoogleSearchAPIWrapper = Field(default_factory=lambda: GoogleSearchAPIWrapper(k=1))
	limiter: AsyncLimiter = None
	google_cse_id: str = None
	google_api_key: str = None
	service_url: str = "https://www.googleapis.com/customsearch/v1"

	def __init__(self, name: str = "google_search",
				 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",):
		super().__init__(name=name, description=description)
		self.google_api_key = os.getenv("GOOGLE_API_KEY")
		self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
		self.limiter = AsyncLimiter(max_rate=2, time_period=2)  # 每秒最多80次请求
	
	def _run(self, query: str) -> list[dict]:
		"""
		Run query through GoogleSearch and return metadata.
		
		Args:
			query: The query to search for.
			
		Returns:
			list[dict]: A list of dictionaries with the following keys:
				snippet - The description of the result.
				title - The title of the result.
				link - The link to the result.
				Or a list containing a single dictionary with the key "Result" if no results are found.
		"""
		if query in self.cache:
			return self.cache[query]
		else:
			try:
				result: list = self.google.results(query=query, num_results=3)
				self.cache[query] = result
			except Exception as e:
				print(str(e))
				return [{"Result": "No results found"}]
		return result
	
	async def _arun(self, query: str, num_results: int = 3) -> list[dict]:
		"""
		Asynchronously fetch search results from Google Search.
		
		Args:
			query: The query to search for.
			num_results: The number of results to return.
		
		Returns:
			str | list[dict]: A list of dictionaries containing search results".
		"""
		try:
			result = await self.aresults(query=query, num_results=num_results)
		except Exception as e:
			print(f"Failed to retrieve data from Google Search: {str(e)}")
			return [{"title": "No results found", "snippet": "", "link": ""}]
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
		try:
			results: List = await self._agoogle_search_results(query, nums=num_results)
		except Exception as e:
			raise e
		if len(results) == 0:
			return [{"title": "No results found", "snippet": "", "link": ""}]
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
		"""
		Asynchronously fetch search results from Google Search.
		
		Args:
			query: The query to search for.
			nums: The number of results to return.
		
		Returns:
			List[dict]: A list of dictionaries containing search results.
			
		Raises:
			Exception: If the maximum number of retries is reached or there is an error fetching the results.
			"""
		if query in self.cache:
			return self.cache[query]
		else:
			params = {
				"q": query,
				"cx": self.google_cse_id,
				"key": self.google_api_key,
				"num": nums,
			}
			retries = 0
			async with self.limiter:
				async with aiohttp.ClientSession() as session:
					while retries < 3:
						try:
							async with session.get(self.service_url, params=params) as response:
								# 处理成功的请求，返回数据
								response.raise_for_status()  # 如果有其他HTTP错误（如500等），会抛出异常
								data = await response.json()
								data = data.get("items", [])
								# 缓存并返回结果
								self.cache[query] = data
								return data
						
						except asyncio.TimeoutError:
							retries += 1
							logging.warning(f"Timeout error occurred, retrying {retries}...")
							await asyncio.sleep(2 ** retries)  # 指数回退
						except aiohttp.ClientError as e:
							retries += 1
							logging.warning(f"Client error occurred: {str(e)}, retrying {retries}...")
							await asyncio.sleep(2 ** retries)
						except Exception as e:
							retries += 1
							logging.error(f"Unexpected error occurred: {str(e)}, retrying {retries}...")
							await asyncio.sleep(2 ** retries)
			
			# 达到最大重试次数后抛出RateLimitExceededError
			raise Exception(f"Rate limit exceeded or persistent error after {retries} retries.")


# class GoogleSearchTool(BaseTool):
# 	name: str = "google_search"
# 	description: str = (
# 		"A wrapper around Google Search. "
# 		"Useful for when you need to answer questions about current events. "
# 		"Input should be a search query."
# 	)
# 	api_wrapper: GoogleSearchAPIWrapper
# 	cache: dc.Cache = Field(default_factory=lambda: dc.Cache(".cache/google_search_tool"))
# 	limiter: AsyncLimiter = None
#
# 	def __init__(self, **kwargs):
# 		super().__init__(**kwargs)
# 		self.limiter = AsyncLimiter(max_rate=2, time_period=2)  # 每秒最多1次请求
#
# 	def _run(self, query: str, run_manager=None,) -> dict | str:
# 		if query in self.cache:
# 			return self.cache[query]
# 		else:
# 			try:
# 				result = self.api_wrapper.run(query=query)
# 				self.cache[query] = result
# 				return result
# 			except Exception as e:
# 				print("GoogleSearchTool._run", str(e))
# 				return "Google Search Error"
#
# 	async def _arun(self, query: str) -> str | list[dict]:
# 		if query in self.cache:
# 			return self.cache[query]
# 		async with self.limiter:
# 			current_time = time.strftime("%H:%M:%S", time.localtime())
# 			print(current_time)
# 			result = await asyncio.to_thread(self.api_wrapper.run, query)
# 			self.cache[query] = result
# 		return result
#
# 	async def aresults(self, query: str) -> str | list[dict]:
# 		if query in self.cache:
# 			return self.cache[query]
# 		async with self.limiter:
# 			result = await asyncio.to_thread(self.api_wrapper.results, query, 3, None)
# 			self.cache[query] = result
# 		return result


async def async_main():
	# 假设 GoogleSearchTool 已经被正确定义
	google_search_tool = GoogleSearchTool()
	
	async def test_arun(index: int):
		query = f"Test Query {index}"  # 每个任务的查询稍有不同
		print(f"Task {index} started.")
		result = await google_search_tool._arun(query)
		print(f"Task {index} completed with result: {result}")
		return result
	
	start_time = time()
	
	# 创建多个任务以测试并发
	num_tasks = 20  # 总任务数
	tasks = [test_arun(i) for i in range(num_tasks)]
	
	# 使用 asyncio.gather 执行所有任务
	results = await asyncio.gather(*tasks)
	
	end_time = time()
	elapsed_time = end_time - start_time
	print(f"Executed {num_tasks} tasks in {elapsed_time:.2f} seconds.")
	return results


def main():
	google_search_tool = GoogleSearchTool()
	query = "Test Query"
	result = google_search_tool.run(query)
	print(result)


if __name__ == "__main__":
	# asyncio.run(async_main())
	main()
