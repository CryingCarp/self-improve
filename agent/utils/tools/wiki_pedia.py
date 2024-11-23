import asyncio
from typing import Dict

import aiohttp
import diskcache as dc
from aiolimiter import AsyncLimiter
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import Field


class WikipediaTool(WikipediaQueryRun):
	name: str = "wikipedia"
	
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(".cache/wikipedia_tool"))
	session: aiohttp.ClientSession = None  # Add this to store the session
	limiter: AsyncLimiter = None
	
	def __init__(self, api_wrapper: WikipediaAPIWrapper = WikipediaAPIWrapper(top_k_results=3),
	             cache_dir: str = ".cache/wikipedia_tool"):
		super().__init__(api_wrapper=api_wrapper)
		self.cache = dc.Cache(cache_dir)
		self.session = aiohttp.ClientSession()
		self.limiter = AsyncLimiter(max_rate=500, time_period=3600)  # 每秒最多200次请求
		
	
	def _run(self, query: str, run_manager=None, ) -> str:
		if query in self.cache:
			return self.cache[query]
		
		try:
			results = self.api_wrapper.run(query)  # 执行 API 请求
			self.cache[query] = results
			return results  # 请求成功，返回结果
		except Exception as e:
			print(f"Error occurred: {e}")
			return (f"Error: {e}")
	
	async def _arun(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		try:
			async with self.limiter:
				results = await asyncio.to_thread(self.api_wrapper.run, query)
				self.cache[query] = results
		except Exception as e:
			print(e)
			return f"Error: {e}"
		return results
	
	async def asummary(self):
		"""
		Plain text summary of the page.
		"""
		if not getattr(self, "_summary", False):
			query_params: Dict[str, str | int] = {
				"prop": "extracts",
				"explaintext": "",
				"exintro": "",
			}
			query_params.update(self.__title_query_param)
			
			request = self.request(query_params)
			self._summary: str = request["query"]["pages"][self.pageid]["extract"]
		
		return self._summary


def main():
	pass


# wikipedia = WikipediaTool()
# query = "Kiss and Tell 1945"
# result = wikipedia.run(query)
# print(result)
	


if __name__ == '__main__':
	main()
