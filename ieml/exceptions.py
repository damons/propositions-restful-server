
### These exeception are raised by the AST

class ASTException(Exception):
    pass

class TermException(ASTException):

    def __init__(self, terms_ieml):
        super().__init__()
        self.terms_ieml = terms_ieml

class IEMLTermNotFoundInDictionnary(TermException):
    pass

### These exceptions /errors are graph_related

class InvalidPropositionGraph(Exception):
    pass


class InvalidWord(InvalidPropositionGraph):
    pass


class IndistintiveTermsExist(InvalidWord):
    pass


class EmptyWordSubstance(InvalidPropositionGraph):
    pass


class NoRootNodeFound(InvalidPropositionGraph):
    pass


class SeveralRootNodeFound(InvalidPropositionGraph):
    pass


class InvalidSingleNode(InvalidPropositionGraph):

    def __init__(self, node_id):
        super().__init__()
        self.node_id = node_id


class NodeHasNoParent(InvalidSingleNode):
    pass


class NodeHasTooMuchParents(InvalidSingleNode):
    pass