import diskcache as dc
from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper
from pydantic import Field

_ = load_dotenv(find_dotenv())

class GoogleSearchTool(BaseTool):
	cache: dc.Cache = Field(default_factory=lambda: dc.Cache(".cache/google_search_tool"))
	google: GoogleSearchAPIWrapper = Field(default_factory=lambda: GoogleSearchAPIWrapper(k=1))
	def __init__(self, name: str = "google_search",
				 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",):
		super().__init__(name=name, description=description)
	
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
	
	async def _arun(self, query: str) -> dict | str:
		return self._run(query=query)


def main():
	google_search = GoogleSearchTool()
	query = "What government position was held by the woman who portrayed Corliss Archer in the film Kiss and Tell"
	result = google_search.run(query)
	print(result)

if __name__ == '__main__':
	main()
