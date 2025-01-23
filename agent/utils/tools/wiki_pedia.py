import asyncio
import os
from typing import Dict

import aiohttp
import diskcache as dc
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv, find_dotenv
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import Field

_ = load_dotenv(find_dotenv())


class WikipediaTool(WikipediaQueryRun):
	name: str = "wikipedia"
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(
		"/Users/ariete/Projects/self-improve/agent/inference/.cache/wikipedia_tool"))
	limiter: AsyncLimiter = None
	service_url: str = "https://en.wikipedia.org/w/api.php"
	headers: Dict = None
	
	def __init__(self, api_wrapper: WikipediaAPIWrapper = WikipediaAPIWrapper(top_k_results=3),
	             cache_dir: str = "/Users/ariete/Projects/self-improve/agent/inference/.cache/wikipedia_tool"):
		super().__init__(api_wrapper=api_wrapper)
		self.cache = dc.Cache(cache_dir)
		self.limiter = AsyncLimiter(max_rate=10, time_period=10)  # 每秒最多200次请求
		self.headers = {
			'User-Agent': 'wikipedia (https://github.com/goldsmith/Wikipedia/)',
			'Authorization': os.environ.get('WIKIMEIDA_API_KEY')
		}
		
	
	def _run(self, query: str, run_manager=None, ) -> str:
		if query in self.cache:
			return self.cache[query]
		try:
			results = self.api_wrapper.run(query)  # 执行 API 请求
			self.cache[query] = results
			return results  # 请求成功，返回结果
		except Exception as e:
			print(f"WikiPedia Error occurred: {e}")
			return f"Error: {e}"
	
	async def _arun(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		try:
			title_pageid_list = await self._fetch_title_pageid(query)
			tasks = [self._async_fetch_summary(title=title_pageid['title'], pageid=title_pageid['pageid']) for
			         title_pageid in title_pageid_list[:3]]
			results = await asyncio.gather(*tasks)
			self.cache[query] = "\n\n".join(results)
			return "\n\n".join(results)
		except Exception as e:
			print(f"WikiPedia Error occurred: {e}")
			return f"Error: {e}"
	
	async def _async_wiki_request(self, params):
		params['format'] = 'json'
		if not 'action' in params:
			params['action'] = 'query'
		retries = 0
		while retries < 3:
			try:
				async with self.limiter:
					async with aiohttp.ClientSession() as session:
						async with session.get(self.service_url, params=params, headers=self.headers) as response:
							return await response.json()
			except Exception as e:
				retries += 1
				if retries >= 3:
					raise RuntimeError(f"Failed WikiPedia after 3 retries: {e}") from e
				await asyncio.sleep(2 ** retries)
	
	async def _fetch_title_pageid(self, query: str) -> list[Dict]:
		"""
		获取查询结果的标题和 pageid
		
		Args:
			query (str): 查询字符串
			
		Returns:
			list[Dict]: 包含查询结果的标题和 pageid 的字典列表
		"""
		assert isinstance(query, str)
		params = {
			'list': 'search',
			'srprop': '',
			'srlimit': 10,
			"action": "query",
			"format": "json",
			"srsearch": query
		}
		try:
			meta_results = await self._async_wiki_request(params)
		except Exception as e:
			raise RuntimeError(f"Failed to fetch title and pageid: {e}") from e
		
		results = [{'title': result['title'], 'pageid': result['pageid']} for result in meta_results['query']['search']]
		return results
	
	async def _async_fetch_summary(self, title: str = None, pageid=None) -> str:
		"""
		获取指定页面的摘要
		
		Args:
			title (str): 页面标题
			pageid ([type]): 页面 ID
			
		Returns:
			str: 页面摘要
		"""
		
		assert title and pageid
		query_params = {
			'prop': 'extracts',
			'explaintext': '',
			'exintro': '',
		}
		if title:
			query_params['titles'] = title
		else:
			query_params['pageids'] = pageid
		
		try:
			meta_results = await self._async_wiki_request(query_params)
			summary = meta_results['query']['pages'][str(pageid)]['extract']
		except Exception as e:
			raise RuntimeError(f"Failed to fetch summary from WikiPedia: {e}") from e
		
		return f"Page: {title}\nSummary: {summary}"


def main():
	wikipedia = WikipediaTool()
	query = "Kiss123"
	result = wikipedia.run(query)
	print(result)
	pass


async def async_main():
	wikipedia = WikipediaTool()

# 假设已经定义了 WikidataTool 类，并且 api_wrapper 和相关方法是正确定义的
	async def test_arun(i):
		query = f"Item {i}"  # 构造一个示例查询
		results = await wikipedia.arun(query)
		return results

	num_tasks = 20  # 测试的并发任务数
	queries = [f"Item {i}" for i in range(1040, 1041)]

	start_time = time()

	# 创建任务列表
	tasks = [test_arun(queries[i]) for i in range(len(queries))]

	# 执行所有任务
	results = await asyncio.gather(*tasks)

	end_time = time()

	# 计算并输出执行时间
	elapsed_time = end_time - start_time
	print(f"Executed {num_tasks} tasks in {elapsed_time:.2f} seconds.")

	# 输出部分结果进行检查
	for result in results:
		print(result)
	


if __name__ == '__main__':
	# main()
	asyncio.run(async_main())
