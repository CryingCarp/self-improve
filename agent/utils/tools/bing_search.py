import diskcache as dc
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
from langchain_community.utilities import BingSearchAPIWrapper
from langchain_core.tools import BaseTool

from pydantic import Field

_ = load_dotenv(find_dotenv())


class BingSearchTool(BaseTool):
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(".cache/bing_search_tool"))
	bing: BingSearchAPIWrapper = Field(init=True, default_factory=lambda: BingSearchAPIWrapper(k=1))
	
	def __init__(self, name: str = "bing_search",
	             description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",
	             cache_dir: str = ".cache/bing_search_tool"):
		super().__init__(name=name, description=description, cache_dir=cache_dir)
		self.cache = dc.Cache(cache_dir)
		self.bing = BingSearchAPIWrapper()
	
	def _run(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		else:
			results = self.bing.results(query=query, num_results=1)
			for result in results:
				result["snippet"] = BeautifulSoup(result["snippet"], "html.parser").get_text()
				result["title"] = BeautifulSoup(result["title"], "html.parser").get_text()
				result.pop("link")
			self.cache[query] = results
		return results
	
	async def _arun(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		else:
			results = self.bing.results(query=query, num_results=1)
			for result in results:
				result["snippet"] = BeautifulSoup(result["snippet"], "html.parser").get_text()
				result["title"] = BeautifulSoup(result["title"], "html.parser").get_text()
				result.pop("link")
			self.cache[query] = results
		return results


def main():
	bing_search = BingSearchTool()
	query = "Kiss and Tell 1945 cast"
	result = bing_search.run(query)
	print(result)


if __name__ == '__main__':
	main()
