import diskcache as dc
from dotenv import load_dotenv, find_dotenv
from langchain_community.tools.wikidata.tool import WikidataAPIWrapper, WikidataQueryRun

_ = load_dotenv(find_dotenv())


class WikidataTool(WikidataQueryRun):
	name: str = "wikidata"
	
	cache: dc.Cache = None
	
	def __init__(self, api_wrapper: WikidataAPIWrapper = WikidataAPIWrapper(top_k=5),
	             cache_dir: str = ".cache/wikidata_tool",
	             description: str = """Wrapper around the Wikidata API.
                                    This wrapper will use the Wikibase APIs to conduct searches and
                                    fetch item content. Always remember that the input to the Wikidata API should be a single phrase or entity!
                                    """):
		super().__init__(api_wrapper=api_wrapper)
		self.cache = dc.Cache(cache_dir)
	
	def _run(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		results = super()._run(query)
		self.cache[query] = results
		
		return results
	
	def _arun(self, query: str) -> str:
		if query in self.cache:
			return self.cache[query]
		results = super()._run(query)
		self.cache[query] = results
		
		return results


def main():
	wikidata = WikidataTool()
	
	print(wikidata.run("Kiss and Tell (1945 film)"))


if __name__ == "__main__":
	main()
