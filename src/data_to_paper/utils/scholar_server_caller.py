class ScholarServer:
    def __init__(self, server: str):
        self.server = server

    def get_server_instance(self):
        """
        Get the server instance.
        """
        if self.server == "Crossref":
            from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER

            return CROSSREF_SERVER_CALLER
        else:
            from data_to_paper.servers.semantic_scholar import (
                SEMANTIC_SCHOLAR_SERVER_CALLER,
            )

            return SEMANTIC_SCHOLAR_SERVER_CALLER
