import os

import diskcache as dc
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import TextCategory, AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
from googleapiclient import discovery
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import BraveSearchWrapper
from langchain_core.tools import BaseTool
from pydantic import Field

_ = load_dotenv(find_dotenv())

    
class BraveSearchTool(BaseTool):
    cache: dc.Cache = Field(init=True)
    brave: BraveSearchWrapper = Field(init=True)
    def __init__(self, name: str = "brave_search", 
                 description: str = "A search engine. useful for when you need to answer questions about current events. Input should be a search query. ", 
                 cache_dir: str = ".cache/brave_search_tool", api_key: str = None, search_kwargs: dict = {"count": 1}):
        super().__init__(name=name, description=description, cache_dir=cache_dir)
        self.cache = dc.Cache(cache_dir)
        self.brave = BraveSearchWrapper(api_key=api_key, search_kwargs=search_kwargs or {})
    
    def _run(self, query: str) -> str:
        if query in self.cache:
            results = self.cache[query]
        else:
            results = self.brave.run(query=query)
            for result in results:
                result["snippet"] = BeautifulSoup(result["snippet"], "html.parser").get_text()
                result["title"] = BeautifulSoup(result["title"], "html.parser").get_text()
                result.pop("link")
            self.cache[query] = results
        return results


class PerspectiveTool(BaseTool):
    name = "perspective"
    description = ("This tool analyzes text for safety using Google Perspective API"
                   "It detects categories such as hate, self-harm, sexual content, and violence. "
                   "Useful when you need to analyze text for safety. "
                   "Input should be a text string."
                   )
    # api_key: str = Field(default=os.environ.get("PERSPECTIVE_API_KEY"), description="Google Perspective API key")
    client: discovery.Resource = Field(init=True)
    cache: dc.Cache = Field(init=True)

    def __init__(self, api_key: str=os.environ.get("GOOGLE_PERSPECTIVE_API_KEY"), cache_dir: str = ".cache/perspective_tool"):
        super().__init__()
        self.client = discovery.build("commentanalyzer", "v1alpha1", 
                                      discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                                      developerKey=api_key,
                                      static_discovery=False,)
        self.cache = dc.Cache(cache_dir)
        
    def _run(self, text: str):
        if text in self.cache:
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
    name: str = "azure_content_moderation"
    description = (
        "This tool analyzes text for safety using Azure AI Content Safety. "
        "It detects categories such as hate, self-harm, sexual content, and violence. "
        "Input should be a text string. "
    )

    key: str = Field(default=os.environ.get("AZURE_CONTENT_SAFETY_KEY"), description="Azure Content Safety API key")
    endpoint: str = Field(default=os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT"), description="Azure Content Safety endpoint")
    client: ContentSafetyClient = Field(init=True)
    cache: dc.Cache = Field(init=True)

    def __init__(self, endpoint: str = None, key: str = None, cache_dir: str = ".cache/azure_content_moderation_tool"):
        super().__init__(key=key, endpoint=endpoint)
        self.client = ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))
        self.cache = dc.Cache(cache_dir)

    def _run(self, text: str) -> str:
        if text in self.cache:
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

class TavilySearch(BaseTool):
    cache: dc.Cache = Field(init=True)
    tavily: TavilySearchResults = Field(init=True)
    def __init__(self, name: str = "tavily_search", description: str = (
                    "A search engine optimized for comprehensive, accurate, and trusted results. "
                    "Useful for when you need to answer questions about current events. "
                    "Input should be a search query."
                ),
                  cache_dir: str = ".cache/tavily_search_tool"):
        super().__init__(name=name, description=description, cache_dir=cache_dir)
        self.cache = dc.Cache(cache_dir)
        self.tavily = TavilySearchResults(max_results=1, search_depth="advanced", include_answer=True, include_raw_content=True)
    def _run(self, query: str) -> str:
        if query in self.cache:
            return self.cache[query]
        else:
            result = self.tavily.run(tool_input=query)[0]
            self.cache[query] = result
        return result

def construct_tools():
    return [
        TavilySearch(),
        BraveSearchTool(api_key=os.environ.get("BRAVE_API_KEY")),
        WikipediaTool(),
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


def main():
    pass
    google_search = GoogleSearchTool()
    print(google_search.run("US"))
    # tavily = TavilySearch()
    # print(tavily.run("University of Louisville game results January 2, 2012"))
    # bing_search = BingSearchTool()
    # print(bing_search.run("how to make steak recipe"))
    # brave = BraveSearchTool(api_key=os.environ.get("BRAVE_API_KEY"))
    # print(brave.run("Louisville Cardinals basketball January 2 2012 game summary and venue"))
    # azure_content_moderation = AzureContentModerationTool(endpoint=os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT"), key=os.environ.get("AZURE_CONTENT_SAFETY_KEY"))
    # print(azure_content_moderation.run("I hate you"))
    # wikipedia = WikipediaTool()
    # print(wikipedia.run("2011–12 Louisville Cardinals men's basketball team"))
    # google_knowledge_graph = GoogleKnowledgeGraphTool(api_key=os.environ.get("GOOGLE_API_KEY"))
    # google_knowledge_graph.run("China")
    # calculator = CalculatorTool()
    # calculator.run("2+2")
    # python_repl = PythonREPLTool()
    # python_repl.run("print('Hello, World!')")
    # perspective = PerspectiveTool()
    # print(perspective.run("I hate you"))


if __name__ == "__main__":
    main()
