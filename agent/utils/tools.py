from pydantic import Field
from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.utilities import BingSearchAPIWrapper, BraveSearchWrapper, WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools.wikidata.tool import WikidataAPIWrapper, WikidataQueryRun
import requests

import numexpr as ne 
from langchain_experimental.utilities import PythonREPL

from googleapiclient import discovery
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import TextCategory, AnalyzeTextOptions
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.exceptions import HttpResponseError

from bs4 import BeautifulSoup

import diskcache as dc
import os
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())


class GoogleSearchTool(BaseTool):
    cache = Field(init=True)
    google = Field(init=True)
    def __init__(self, name: str = "google_search", description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",
                  cache_dir: str = ".cache/google_knowledge_graph_tool"):
        super().__init__(name=name, description=description, cache_dir=cache_dir)
        self.cache = dc.Cache(cache_dir)
        self.google = GoogleSearchAPIWrapper()

    def _run(self, query: str) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            return self.cache[query]
        else:
            result = self.google.results(query=query, num_results=1)[0]
            self.cache[query] = result
        return result

class BingSearchTool(BaseTool):
    cache = Field(init=True)
    bing = Field(init=True)
    def __init__(self, name: str = "bing_search", description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ",
                 cache_dir: str = ".cache/bing_search_tool"):
        super().__init__(name=name, description=description, cache_dir=cache_dir)
        self.cache = dc.Cache(cache_dir)
        self.bing = BingSearchAPIWrapper()

    def _run(self, query: str) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            return self.cache[query]
        else:
            result = self.bing.results(query=query, num_results=1)[0]
            result["snippet"] = BeautifulSoup(result["snippet"], "html.parser").get_text()
            result["title"] = BeautifulSoup(result["title"], "html.parser").get_text()
            self.cache[query] = result
        return result
    
class BraveSearchTool(BaseTool):
    cache = Field(init=True)
    brave = Field(init=True)
    def __init__(self, name: str = "brave_search", 
                 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ", 
                 cache_dir: str = ".cache/brave_search_tool", api_key: str = None, search_kwargs: dict = {"count": 1}):
        super().__init__(name=name, description=description, cache_dir=cache_dir)
        self.cache = dc.Cache(cache_dir)
        self.brave = BraveSearchWrapper(api_key=api_key, search_kwargs=search_kwargs or {})
    
    def _run(self, query: str) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            result = self.cache[query]
        else:
            result = self.brave.run(query=query)[0]
            self.cache[query] = result

        result['snippet'] = BeautifulSoup(result['snippet'], "html.parser").get_text()
        return result

class WikidataTool(WikidataQueryRun):
    name = "wikidata"

    cache = Field(init=True)

    def __init__(self, api_wrapper: WikidataAPIWrapper = WikidataAPIWrapper(), cache_dir: str = ".cache/wikidata_tool"):
        super().__init__(api_wrapper=api_wrapper)
        self.cache = dc.Cache(cache_dir)

    def _run(self, query: str) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            return self.cache[query]
        
        results = super()._run(query)

        self.cache[query] = results
        
        return results

class WikipediaTool(WikipediaQueryRun):
    name = "wikipedia"

    cache = Field(init=True)

    def __init__(self, api_wrapper: WikipediaAPIWrapper = WikipediaAPIWrapper(top_k_results=1), cache_dir: str = ".cache/wikipedia_tool"):
        super().__init__(api_wrapper=api_wrapper)
        self.cache = dc.Cache(cache_dir)

    def _run(self, query: str) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            return self.cache[query]
        
        results = super()._run(query)

        self.cache[query] = results
        
        return results
    
class GoogleKnowledgeGraphTool(BaseTool):
    name = "google_knowledge_graph"
    description = (
        "This tool searches for entities in the Google Knowledge Graph. "
        "It provides information about people, places, things, and concepts. "
        "Useful when you need to get information about a specific entity. "
        "Input should be an entity name."
    )
    api_key: str = Field(..., description="Google Knowledge Graph Search API key")
    cache = Field(init=True)

    def __init__(self, api_key: str, cache_dir: str = ".cache/google_knowledge_graph_tool"):
        super().__init__(api_key=api_key)
        self.cache = dc.Cache(cache_dir)

    def _run(self, query: str, limit: int = 1) -> str:
        if query in self.cache:
            print("Cache hit for text:", query)
            return self.cache[query]

        service_url = "https://kgsearch.googleapis.com/v1/entities:search"
        params = {
            "query": query,
            "limit": limit,
            "indent": True,
            "key": self.api_key,
        }

        try:
            response = requests.get(service_url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.RequestException as e:
            return f"Failed to retrieve data: {str(e)}"

        data = response.json()
        self.cache[query] = data
        return data

    def _format_results(self, data: dict) -> str:
        results = data.get("itemListElement", [])
        formatted_results = []

        for element in results:
            result = element.get("result", {})
            name = result.get("name", "N/A")
            score = element.get("resultScore", 0)
            formatted_results.append(f"{name} ({score})")

        return "\n".join(formatted_results) if formatted_results else "No results found."

class CalculatorTool(BaseTool):
    name = "calculator"
    description = ("Useful when you need to calculate the value of a mathematical expression, including basic arithmetic operations. "
                   "Use this tool for math operations. "
                   "Input should strictly follow the numuxpr syntax. ")

    def _run(self, expression: str):
      try:
        result = ne.evaluate(expression).item()
        return f"The result of the expression of <{expression}> is: {result}."
      except Exception as e:
        # return "This is not a numexpr valid syntax. Try a different syntax."
        return f"Error in calculation: {str(e)}"
      
class PythonREPLTool(BaseTool):
    name = "python_repl"
    description = ("A Python shell. Use this to execute python code. It could also be used as a calculator. "
                   "Input should be a valid python code. "
                   "If you want to see the output of a value, you should print it out with `print(...)`.")
    def _run(self, code: str) -> str:
        try:
            result = PythonREPL().run(code)
            return result
        except Exception as e:
            return f"Error: {str(e)}"

class PerspectiveTool(BaseTool):
    name = "perspective"
    description = ("This tool analyzes text for safety using Google Perspective API"
                   "It detects categories such as hate, self-harm, sexual content, and violence. "
                   "Useful when you need to analyze text for safety. "
                   "Input should be a text string."
                   )
    # api_key: str = Field(default=os.environ.get("PERSPECTIVE_API_KEY"), description="Google Perspective API key")
    client = Field(init=True)
    cache = Field(init=True)

    def __init__(self, api_key: str=os.environ.get("GOOGLE_PERSPECTIVE_API_KEY"), cache_dir: str = ".cache/perspective_tool"):
        super().__init__()
        self.client = discovery.build("commentanalyzer", "v1alpha1", 
                                      discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                                      developerKey=api_key,
                                      static_discovery=False,)
        self.cache = dc.Cache(cache_dir)
        
    def _run(self, text: str):
        if text in self.cache:
            print("Cache hit for text:", text)
            return self.cache[text]

        PERSPECTIVE_API_ATTRIBUTES = (
            'TOXICITY',
            'SEVERE_TOXICITY',
            'IDENTITY_ATTACK',
            'INSULT',
            'THREAT',
            'PROFANITY',
            'SEXUALLY_EXPLICIT',
            'FLIRTATION'
        )

        analyze_request = {
            'comment': {'text': text},
            'requestedAttributes': {attr: {} for attr in PERSPECTIVE_API_ATTRIBUTES}
        }

        response = self.client.comments().analyze(body=analyze_request).execute()
        # Cache the result
        self.cache[text] = response
        return response

class AzureContentModerationTool(BaseTool):
    name = "azure_content_moderation"
    description = (
        "This tool analyzes text for safety using Azure AI Content Safety. "
        "It detects categories such as hate, self-harm, sexual content, and violence. "
        "Input should be a text string. "
    )

    key: str = Field(default=os.environ.get("AZURE_CONTENT_SAFETY_KEY"), description="Azure Content Safety API key")
    endpoint: str = Field(default=os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT"), description="Azure Content Safety endpoint")
    client: ContentSafetyClient = Field(init=True)
    cache = Field(init=True)

    def __init__(self, endpoint: str = None, key: str = None, cache_dir: str = ".cache/azure_content_moderation_tool"):
        super().__init__(key=key, endpoint=endpoint)
        self.client = ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))
        self.cache = dc.Cache(cache_dir)

    def _run(self, text: str) -> str:
        if text in self.cache:
            print("Cache hit for text:", text)
            return self.cache[text]
        
        request = AnalyzeTextOptions(text=text)

        try:
            response = self.client.analyze_text(request)
        except HttpResponseError as e:
            error_message = "Analyze text failed."
            if e.error:
                error_message += f" Error code: {e.error.code}. Error message: {e.error.message}"
            return error_message

        results = {
            "hate": self._get_severity(response, TextCategory.HATE),
            "self_harm": self._get_severity(response, TextCategory.SELF_HARM),
            "sexual": self._get_severity(response, TextCategory.SEXUAL),
            "violence": self._get_severity(response, TextCategory.VIOLENCE),
        }

        formatted_results = self._format_results(results)

        self.cache[text] = formatted_results

        return formatted_results

    def _get_severity(self, response, category: TextCategory):
        result = next((item for item in response.categories_analysis if item.category == category), None)
        return result.severity if result else "Not found"

    def _format_results(self, results: dict) -> str:
        return "\n".join(f"{category.capitalize()} severity: {severity} outof 7." for category, severity in results.items())

def construct_tools():
    return [
        GoogleSearchTool(),
        BingSearchTool(),
        BraveSearchTool(api_key=os.environ.get("BRAVE_API_KEY")),
        WikidataTool(),
        WikipediaTool(),
        GoogleKnowledgeGraphTool(api_key=os.environ.get("GOOGLE_API_KEY")),
        CalculatorTool(),
        PythonREPLTool(),
        PerspectiveTool(),
        AzureContentModerationTool(endpoint=os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT"), key=os.environ.get("AZURE_CONTENT_SAFETY_KEY"))
    ]

def get_tools_descriptions(tools:list):
    tools_descriptions = []
    for tool in tools:
        tools_descriptions.append(f"{tool.name} - {tool.description}")
    return "\n\n".join(tools_descriptions)

def get_tools_dict(tools:list)->dict:
    tools_dict = {}
    for tool in tools:
        tools_dict[tool.name.lower()] = tool
    return tools_dict


if __name__ == "__main__":
    google_search = GoogleSearchTool()
    print(google_search.run("University of Louisville game results January 2, 2012"))
    bing_search = BingSearchTool()
    print(bing_search.run("how to make steak recipe"))
    brave = BraveSearchTool(api_key=os.environ.get("BRAVE_API_KEY"))
    print(brave.run("Louisville Cardinals basketball January 2 2012 game summary and venue"))
    azure_content_moderation = AzureContentModerationTool(endpoint=os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT"), key=os.environ.get("AZURE_CONTENT_SAFETY_KEY"))
    print(azure_content_moderation.run("I hate you"))
    wikidata = WikidataTool()
    print(wikidata.run("University of Louisville game January 2, 2012"))
    wikipedia = WikipediaTool()
    print(wikipedia.run("2011–12 Louisville Cardinals men's basketball team"))
    google_knowledge_graph = GoogleKnowledgeGraphTool(api_key=os.environ.get("GOOGLE_API_KEY"))
    google_knowledge_graph.run("China")
    calculator = CalculatorTool()
    calculator.run("2+2")
    python_repl = PythonREPLTool()
    python_repl.run("print('Hello, World!')")
    perspective = PerspectiveTool()
    print(perspective.run("I hate you"))