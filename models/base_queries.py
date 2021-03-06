from random import randint
import re
from pymongo import MongoClient

from helpers.metaclasses import Singleton
from models.constants import TERMS_COLLECTION, TAG_LANGUAGES, DB_NAME_TERM
from .constants import DB_ADDRESS, DB_NAME


class DBConnector(object, metaclass=Singleton):
    """Automatically connects when instantiated"""

    def __init__(self):
        self.client = MongoClient(DB_ADDRESS)  # connecting to the db

        self.db = self.client[DB_NAME] # opening a DB
        self.db_term = self.client[DB_NAME_TERM]

        self.terms = self.db_term[TERMS_COLLECTION]

class DictionaryQueries(DBConnector):
    """Class mainly used for anything related to the terms collection, i.e., the dictionnary"""

    def _format_response(self, term):
        return {
            "IEML": '[' + term["IEML"] + ']',
            "TAGS": {
                "FR": term.get("FR"),
                "EN": term.get("EN")},
            "TYPE": "TERM",
            "CANONICAL": term["CANONICAL"],
            "OBJECT_ID": term["_id"]}

    def search_for_terms(self, search_string):
        """Searching for terms containing the search_string, both in the IEML field and translated field"""
        regex = re.compile(re.escape(search_string))

        result = [self._format_response(term)
                  for term in self.terms.find(
                    {'$or': [
                        {'IEML': {'$regex': regex}},
                        {'FR': {'$regex': regex}},
                        {'EN': {'$regex': regex}}]
                    })]
        return result

    def exact_ieml_term_search(self, ieml_string):
        if ieml_string[0] == '[' and ieml_string[-1] == ']':
            ieml_string = ieml_string[1:-1]

        term = self.terms.find_one({"IEML": ieml_string})
        if term:
            return self._format_response(term)
        else:
            return None

    def get_random_terms(self, count):
        """Used by the random proposition generator : ouputs n random terms from the dicitonary DB, n being count"""
        total_count = self.terms.count()
        return [term["IEML"] for term in self.terms.find().limit(count).skip(randint(0, total_count - 1))]

    def search_terms(self, search_string, languages=None, category=None, type=None):
        regex = {'$regex': re.compile(re.escape(search_string))}

        categories = [{'IEML': regex}]
        if languages:
            for language in languages:
                categories.append({language: regex})
        else:
            for language in TAG_LANGUAGES:
                categories.append({language: regex})

        query = {'$or': categories}
        #query['CLASS'] with category
        #query['PARADIGM'] with type

        return [self._format_response(term)
                for term in self.terms.find(query)]

    def check_tags_available(self, tags):
        for language in tags:
            if self.check_tag_exist(tags[language], language):
                return False
        return True

    def check_tag_exist(self, tag, language):
        return self.terms.find_one({language: tag}) is not None


class Tag:
    @staticmethod
    def check_tags(tags):
        return all(lang in tags for lang in TAG_LANGUAGES) and all(tag for tag in tags)
