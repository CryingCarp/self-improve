import diskcache as dc
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import Field


class WikipediaTool(WikipediaQueryRun):
	name: str = "wikipedia"
	
	cache: dc.Cache = Field(init=True, default_factory=lambda: dc.Cache(".cache/wikipedia_tool"))
	
	def __init__(self, api_wrapper: WikipediaAPIWrapper = WikipediaAPIWrapper(top_k_results=3),
	             cache_dir: str = ".cache/wikipedia_tool"):
		super().__init__(api_wrapper=api_wrapper)
		self.cache = dc.Cache(cache_dir)
	
	def _run(self, query: str, run_manager=None, ) -> str:
		if query in self.cache:
			return self.cache[query]
		
		results = super()._run(query)
		
		self.cache[query] = results
		
		return results
	
	async def _arun(self, query: str, run_manager=None, ) -> str:
		if query in self.cache:
			return self.cache[query]
		
		results = super()._run(query)
		
		self.cache[query] = results
		
		return results


def main():
	wikipedia = WikipediaTool()
	query = "Kiss and Tell 1945"
	result = wikipedia.run(query)
	print(result)


if __name__ == '__main__':
	main()
