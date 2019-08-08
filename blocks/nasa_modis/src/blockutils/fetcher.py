"""
Abstract Fetcher class definitions
"""


from .stac import STACQuery

class AbstractFetcher:
    def fetch(self, query: STACQuery, dry_run: bool = False):
        raise NotImplementedError

class AbstractAOIClippedFetcher(AbstractFetcher):
    def fetch(self, query: STACQuery, dry_run: bool = False):
        raise NotImplementedError

class AbstractFullSceneFetcher(AbstractFetcher):
    def fetch(self, query: STACQuery, dry_run: bool = False):
        raise NotImplementedError
