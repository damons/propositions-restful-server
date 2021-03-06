class DBException(Exception):
    pass


class PropositionAlreadyExists(DBException):
    pass


class TextAlreadyExists(DBException):
    pass


class HypertextAlreadyExists(DBException):
    pass


class ObjectTypeNotStoredinDB(DBException):
    pass


class InvalidTags(DBException):
    pass


class ObjectNotFound(DBException):
    pass


class InvalidASTType(DBException):
    pass