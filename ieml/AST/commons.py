from ieml.exceptions import CannotRenderElementWithoutOrdering, PathCannotBeEmpty, CannotRetrieveMetadata
from functools import total_ordering

@total_ordering
class AbstractPropositionMetaclass(type):
    """This metaclass enables the comparison of class times, such as (Sentence > Word) == True"""

    def __gt__(self, other):
        from ieml.AST import Term, Morpheme, Word, Clause, Sentence, SuperClause, SuperSentence
        child_list = [Term, Morpheme, Word, Clause, Sentence, SuperClause, SuperSentence]
        return child_list.index(self) > child_list.index(other)

    def __lt__(self, other):
        from ieml.AST import Term, Morpheme, Word, Clause, Sentence, SuperClause, SuperSentence
        child_list = [Term, Morpheme, Word, Clause, Sentence, SuperClause, SuperSentence]
        return child_list.index(self) < child_list.index(other)


def requires_not_empty(method):
    """Decorator used by propositions paths that checks if the path is not empty"""
    def wrapper(*args, **kwargs):
        if not args[0].path:
            raise PathCannotBeEmpty("This method cannot work on an empty path")
        else:
            return method(*args, **kwargs)
    return wrapper


class PropositionPath:
    """Stores a path to a 'closable' proposition *inside* another closed proposition, in a text.
    Used by hyperlinks to figure out which proposition is the right one"""

    def __init__(self, path=None, proposition=None):
        self.path = []
        if path:
            self.path += path
        if proposition:
            self.path.append(proposition)

    def __str__(self):
        return '/'.join(self.to_ieml_list())

    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
        return self.path == other.path

    def to_ieml_list(self):
        return [str(e) for e in self.path]

    @requires_not_empty
    def get_children_subpaths(self, depth=1): # depth indicate how make times the function should go down
        """Generates the subpaths to the child of a proposition"""
        if depth == 0:
            return [self]
        else:
            result = []
            for child in self.path[-1].children:
                result += PropositionPath(self.path, child).get_children_subpaths(depth - 1)
            return result


class TreeStructure:
    def __init__(self):
        super().__init__()
        self._has_been_checked = False
        self._has_been_ordered = False
        self._str = None
        self._metadata = None
        self.children = None  # will be an iterable (list or tuple)

    def __str__(self):
        if self._str is not None:
            return self._str
        else:
            raise CannotRenderElementWithoutOrdering()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        """Two propositions are equal if their children'list or tuple are equal"""
        return self.children == other.children

    def __hash__(self):
        """Since the IEML string for any proposition AST is supposed to be unique, it can be used as a hash"""
        return self.__str__().__hash__()

    def __iter__(self):
        """Enables the syntaxic sugar of iterating directly on an element without accessing "children" """
        return self.children.__iter__()

    @property
    def level(self):
        """Returns the string level of an IEML object, such as TEXT, WORD, SENTENCE, ..."""
        return self.__class__.__name__.upper()

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self._retrieve_metadata_instance()
            if self._metadata is not None:
                return self._metadata
            else:
                raise CannotRetrieveMetadata("Cannot retrieve metadata for this element")
        else:
            return self._metadata

    def _do_precompute_str(self):
        pass

    def _do_ordering(self):
        pass

    def order(self):
        if self.is_ordered():
            return

        self._do_ordering()
        self._do_precompute_str()
        self._has_been_ordered = True

    def _do_checking(self):
        pass

    def check(self):
        """Checks the IEML validity of the IEML proposition"""
        for child in self.children:
            child.check()
            child.order()

        if self.is_checked():
            return

        self._do_checking()
        self._has_been_checked = True

        self.order()

    def is_checked(self):
        return self._has_been_checked

    def is_ordered(self):
        return self._has_been_ordered



