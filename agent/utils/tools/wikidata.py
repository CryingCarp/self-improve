import asyncio
from time import time

import diskcache as dc
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv, find_dotenv
from langchain_community.tools.wikidata.tool import WikidataQueryRun
from langchain_community.utilities.wikidata import WikidataAPIWrapper

_ = load_dotenv(find_dotenv())


# class AsyncFluentWikibaseClient(FluentWikibaseClient):
# 	async def async_get_item(self, qid: str) -> Optional[FluentWikibaseItem]:
# 		item_response = await get_item.asyncio_detailed(qid, client=self._client)
# 		if item := self._check_response(item_response):
# 			label = (item.labels or EMPTY_STRING_DICT).get(self.lang)
# 			description = (item.descriptions or EMPTY_STRING_DICT).get(self.lang)
# 			aliases = (item.aliases or EMPTY_STRING_DICT).get(self.lang)
# 			statements = dict()
# 			if item.statements:
# 				pids = self._supported_props or item.statements.additional_properties.keys()
# 				for pid in pids:
# 					if pid not in item.statements:
# 						continue
# 					values = item.statements[pid]
# 					if property_label := self._get_property_label(pid):
# 						datatype: Optional[str] = None
#
# 						fluent_values = []
# 						for value in values:
# 							if value.property_:
# 								datatype = value.property_.data_type or None
# 								value_string = self._value_to_string(value.value, value.property_.data_type)
# 								if value_string:
# 									fluent_values.append(value_string)
# 						if fluent_values and datatype:
# 							fluent_property = FluentProperty(pid=pid, label=property_label, datatype=datatype)
# 							statements[fluent_property] = fluent_values
#
# 			return FluentWikibaseItem(
# 				qid=qid,
# 				label=label,
# 				description=description,
# 				aliases=aliases,
# 				statements=statements,
# 			)
# 		return None
#
# class AsyncMediaWikiAPI(MediaWikiAPI):
# 	def __init__(self):
# 		super().__init__(config=Config(user_agent=WIKIDATA_USER_AGENT, mediawiki_url=WIKIDATA_API_URL))
# 		self.async_session = aiohttp.ClientSession()
#
# 	async def async_search(self, query: str, results: int = 10, suggestion: bool = False) -> Union[List[str], Tuple[List[Any], Optional[List[str]]]]:
# 		search_params = {
# 			"list": "search",
# 			"srprop": "",
# 			"srlimit": results,
# 			"limit": results,
# 			"srsearch": query,
# 		}
# 		if suggestion:
# 			search_params["srinfo"] = "suggestion"
# 		raw_results = await self._async_request(params=search_params)
# 		if "error" in raw_results:
# 			if raw_results["error"]["info"] in ("HTTP request timed out.", "Pool queue is full"):
# 				raise HTTPTimeoutError(query)
# 			else:
# 				raise MediaWikiAPIException(raw_results["error"]["info"])
# 		search_results = [d["title"] for d in raw_results["query"]["search"]]
# 		if suggestion:
# 			return search_results, raw_results["query"].get("searchinfo", {}).get("suggestion")
# 		return search_results
#
# 	async def _async_request(self, params: dict, language: Optional[Union[str, Language]] = None):
# 		params["format"] = "json"
# 		if "action" not in params:
# 			params["action"] = "query"
#
# 		headers = {"User-Agent": self.config.user_agent}
# 		try:
# 			async with self.async_session.get(self.config.get_api_url(language), params=params, headers=headers, timeout=self.config.timeout) as response:
# 				response.raise_for_status()
# 				data = await response.json()
# 				return data
# 		except aiohttp.ClientError as e:
# 			print(f"Failed to retrieve data: {str(e)}")
# 			raise e
#
# 	async def close(self):
# 		if self.async_session:
# 			await self.async_session.close()
#
# 	def __del__(self):
# 		if self.async_session:
# 			asyncio.create_task(self.close())
#
# class AsyncWikidataAPIWrapper(WikidataAPIWrapper):
# 	async_wikidata_mw: Any
# 	wikidata_rest: Any
# 	top_k_results: int = 3
# 	doc_content_chars_max: int = 4000
# 	wikidata_props: List[str] = DEFAULT_PROPERTIES
# 	lang: str = DEFAULT_LANG_CODE
#
# 	async def _async_item_to_document(self, qid: str) -> Optional[Document]:
# 		fluent_client = AsyncFluentWikibaseClient(self.wikidata_rest, supported_props=self.wikidata_props, lang=self.lang)
# 		resp = await fluent_client.async_get_item(qid)
# 		if not resp:
# 			return None
# 		doc_lines = [f"Label: {resp.label}", f"Description: {resp.description}", f"Aliases: {', '.join(resp.aliases)}"]
# 		for prop, values in resp.statements.items():
# 			doc_lines.append(f"{prop.label}: {', '.join(values)}")
# 		return Document(
# 			page_content="\n".join(doc_lines)[:self.doc_content_chars_max],
# 			meta={"title": qid, "source": f"https://www.wikidata.org/wiki/{qid}"}
# 		)
#
# 	async def arun(self, query: str) -> str:
# 		items = await self.async_wikidata_mw.async_search(query=query[:WIKIDATA_MAX_QUERY_LENGTH])
# 		raise Exception("123")
# 		docs = [f"Result {item}:\n{(await self._async_item_to_document(item)).page_content}" for item in items[:self.top_k_results] if await self._async_item_to_document(item)]
# 		return "\n\n".join(docs)[:self.doc_content_chars_max] if docs else "No good Wikidata Search Result was found"

# class WikidataTool(BaseTool):
# 	name: str = "wikidata"
# 	description: str = "A wrapper around Wikidata. Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects. Input should be the exact name of the item you want information about or a Wikidata QID."
# 	limiter: AsyncLimiter = AsyncLimiter(max_rate=200, time_period=60)
# 	cache: dc.Cache = dc.Cache(".cache/wikidata_tool")
# 	api_wrapper: AsyncWikidataAPIWrapper = None
#
# 	def __init__(self, **kwargs: Any):
# 		super().__init__(**kwargs)
# 		self.async_wikidata_mw = AsyncMediaWikiAPI()
# 		self.wikidata_rest = Client(
# 				timeout=60,
# 				base_url=WIKIDATA_REST_API_URL,
# 				headers={"User-Agent": WIKIDATA_USER_AGENT},
# 				follow_redirects=True,
# 			)
# 		self.api_wrapper = AsyncWikidataAPIWrapper(async_wikidata_mw=self.async_wikidata_mw, wikidata_rest=self.wikidata_rest)
#
# 	def _run(self, query: str, run_manager=None) -> str:
# 		if query in self.cache:
# 			return self.cache[query]
# 		results = self.api_wrapper.run(query)
# 		self.cache[query] = results
# 		return results
#
# 	async def _arun(self, query: str) -> str:
# 		if query in self.cache:
# 			return self.cache[query]
# 		try:
# 			async with self.limiter:
# 				results = await self.api_wrapper.arun(query)
# 				self.cache[query] = results
# 		except Exception as e:
# 			print(e)
# 			return f"Error: {e}"
# 		return results

class WikidataTool(WikidataQueryRun):
	name: str = "wikidata"
	description: str = "A wrapper around Wikidata. Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects. Input should be the exact name of the item you want information about or a Wikidata QID."
	limiter: AsyncLimiter = AsyncLimiter(max_rate=2, time_period=2)
	cache: dc.Cache = dc.Cache("/Users/ariete/Projects/self-improve/agent/inference/.cache/wikidata_tool")
	
	def _run(self, query: str, run_manager=None) -> str:
		if query in self.cache:
			return self.cache[query]
		try:
			results = self.api_wrapper.run(query)
			self.cache[query] = results
			return results
		except Exception as e:
			print(f"WikiData Failed: {e}")
			return f"Error: {e}"
	
	async def _arun(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		retries = 0
		while retries < 3:
			try:
				async with self.limiter:
					results = await asyncio.to_thread(self.api_wrapper.run, query)
					self.cache[query] = results
					return results
			except Exception as e:
				retries += 1
				if retries >= 3:
					print(f"WikiData Failed after 3 retries: {e}")
					raise RuntimeError(f"Failed after 3 retries: {e}") from e
				await asyncio.sleep(2 ** retries)


async def async_main():
	# 假设已经定义了 WikidataTool 类，并且 api_wrapper 和相关方法是正确定义的
	async def test_arun(i):
		query = f"Item {i}"  # 构造一个示例查询
		results = await wikidata_tool._arun(query)
		return results
	
	# 创建 WikidataTool 实例
	wikidata_tool = WikidataTool(api_wrapper=WikidataAPIWrapper())  # 假设您的 API 包装器已经定义
	
	num_tasks = 20  # 测试的并发任务数
	queries = [f"Item {i}" for i in range(1040, 1060)]
	
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


def main():
	wikidata_tool = WikidataTool(api_wrapper=WikidataAPIWrapper())  # 假设您的 API 包装器已经定义
	query = "Donald Trump"
	results = wikidata_tool.run(query)
	print(results)

if __name__ == "__main__":
	asyncio.run(async_main())
# main()
