import diskcache as dc
from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper
from pydantic import Field

_ = load_dotenv(find_dotenv())

proxies = {
	'http': 'http://127.0.0.1:7897',
	'https': 'http://127.0.0.1:7897',  # 如果需要 HTTPS 代理
}

class GoogleSearchTool(BaseTool):
	cache: dc.Cache = Field(default_factory=lambda: dc.Cache(".cache/google_search_tool"))
	google: GoogleSearchAPIWrapper = Field(default_factory=lambda: GoogleSearchAPIWrapper(k=1))
	def __init__(self, name: str = "google_search",
				 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",):
		super().__init__(name=name, description=description)

	def _run(self, query: str) -> dict:
		if query in self.cache:
			return self.cache[query]
		else:
			result = self.google.results(query=query, num_results=1)[-1]
			self.cache[query] = result
		return result


def main():
	google_search = GoogleSearchTool()
	query = "what is the capital of france"
	result = google_search.run(query)
	print(result)

if __name__ == '__main__':
	main()
