import logging

from ieml import PropositionsParser
from ieml.AST import Word, Sentence, SuperSentence, Morpheme, Term, promote_to
from ieml.AST.tools import SentenceGraph, SuperSentenceGraph
from ieml.exceptions import InvalidNodeIEMLLevel
from models import PropositionsQueries, DictionaryQueries, PropositionAlreadyExists, TextQueries, HyperTextQueries
from .base import BaseHandler, BaseDataHandler, ErrorCatcher
from .exceptions import MissingField,PromotingToInvalidLevel,InvalidIEMLReference, EmptyUslChecking


class ValidatorHandler(BaseDataHandler):
    """Abstract handler for both proposition-related handlers. Factorizes the JSON data field-checking"""

    def __init__(self):
        super().__init__()
        self.db_connector = PropositionsQueries()

    def _build_ieml_ast(self):
        """Using the data from the JSON requests, builds an AST of the IEML object being checked. Returns a
        checked and ordered IEML object"""
        pass

    def _save_closed_proposition(self, closed_proposition_ast):
        self.db_connector.save_closed_proposition(closed_proposition_ast, self.json_data["tags"])


class GraphCheckerHandler(ValidatorHandler):
    """Checks that a give graph representing a sentence/supersentence is well formed, and if it is,
    returns the corresponding IEML string"""

    def do_request_parsing(self):
        super().do_request_parsing()
        for field in ["graph", "nodes", "tags"]:
            if field not in self.json_data:
                raise MissingField(field)

    def _build_ieml_ast(self):
        parser = PropositionsParser()
        if "validation_type" in self.json_data:
            graph_type = SentenceGraph if self.json_data["validation_type"] == 1 else SuperSentenceGraph
        else:
            logging.warning("Couldn't find validation_type field, defaulting to sentence level")
            graph_type = SentenceGraph

        nodes_table = {}
        for node in self.json_data["nodes"]:
            nodes_table[node["id"]] = parser.parse(node["ieml_string"])
            if not isinstance(nodes_table[node["id"]], graph_type.primitive_type):
                nodes_table[node["id"]] = promote_to(nodes_table[node["id"]], graph_type.primitive_type)

        # transforming the vertices into clauses or superclauses
        multiplication_elems = []
        for vertice in self.json_data["graph"]:
            new_element = graph_type.multiplicative_type(nodes_table[vertice["substance"]],
                                                         nodes_table[vertice["attribute"]],
                                                         nodes_table[vertice["mode"]])
            multiplication_elems.append(new_element)

        #OH WAIT, we can make it into a sentence/supersentence now, and return it
        proposition_ast = graph_type.additive_type(multiplication_elems)
        # asking the proposition to check then order itself
        proposition_ast.check()

        return proposition_ast

    @ErrorCatcher
    def post(self):
        self.do_request_parsing()
        # retrieving a checked and ordered proposition
        proposition_ast = self._build_ieml_ast()
        return {"valid": True, "ieml": str(proposition_ast)}


class GraphSavingHandler(GraphCheckerHandler):
    """Checks the graph of a sentence/supersentence is correct (alike the graph checker), and saves it."""

    @ErrorCatcher
    def post(self):
        self.do_request_parsing()
        # retrieving a checked and ordered proposition
        proposition_ast = self._build_ieml_ast()
        # saving it to the database
        self._save_closed_proposition(proposition_ast)
        return {"valid": True, "ieml": str(proposition_ast)}


class WordGraphCheckerHandler(ValidatorHandler):
    """Checks that a give graph representing a word is well formed, and if it is,
    returns the corresponding IEML string"""

    def do_request_parsing(self):
        super().do_request_parsing()
        for field in ["substance", "mode", "tags"]:
            if field not in self.json_data:
                raise MissingField(field)

    def _build_ieml_ast(self):
        parser = PropositionsParser()

        substance_list = [parser.parse(substance) for substance in self.json_data["substance"]]
        mode_list = [parser.parse(mode) for mode in self.json_data["mode"]]

        if len(mode_list) == 0:
            mode = None
        else:
            mode = Morpheme(mode_list)

        if len(substance_list) == 0:
            raise EmptyUslChecking()

        # making the two morphemes and then the word using the two term lists
        word_ast = Word(Morpheme(substance_list), mode)

        # asking the proposition to check itself
        word_ast.check()

        return word_ast

    @ErrorCatcher
    def post(self):
        self.do_request_parsing()
        # retrieving the checked word ast
        word_ast = self._build_ieml_ast()
        return {"valid": True, "ieml": str(word_ast)}


class WordGraphSavingHandler(WordGraphCheckerHandler):
    """Checks the graph of a word is correct (alike the word graph checker), and saves it."""

    @ErrorCatcher
    def post(self):
        self.do_request_parsing()
        # retrieving the checked word ast
        word_ast = self._build_ieml_ast()
        self._save_closed_proposition(word_ast)
        return {"valid": True, "ieml": str(word_ast)}
