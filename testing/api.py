from handlers import WordGraphCheckerHandler, GraphCheckerHandler, TextDecompositionHandler
from .helper import *
from unittest.mock import MagicMock


class TestGraphValidator(unittest.TestCase):

    def setUp(self):
        self.word_handler = WordGraphCheckerHandler()
        self.word_handler.json_data = {"substance": ["[a.i.-]", "[i.i.-]"],
                                       "mode": ["[E:A:T:.]", "[E:S:.wa.-]", "[E:S:.o.-]"],
                                       "tags" : {
                                           "FR": "Faire du bruit avec sa bouche",
                                           "EN": "Blah blah blah"
                                            }
                                       }

        self.word_handler.db_connector = Mock()
        self.word_handler.do_request_parsing = MagicMock(name="do_request_parsing")

    def test_word_validation(self):
        """Tests the whole word validation code block without the request handling"""

        request_output = self.word_handler.post()
        word = get_test_word_instance()
        word.check()
        self.assertEqual(request_output["ieml"], str(word))


class TestSentenceGraphValidator(unittest.TestCase):

    def setUp(self):
        self.sentence_handler = GraphCheckerHandler()
        self.sentence_handler.db_connector = Mock()
        self.sentence_handler.do_request_parsing = MagicMock(name="do_request_parsing")

    def test_sentence_validation(self):
        a, b, c, d, e, f = tuple(get_words_list())
        self.sentence_handler.json_data = {"validation_type" : 1,
                                           "nodes" : [{"id" : 1,
                                                       "ieml_string" : str(a)},
                                                      {"id" : 2,
                                                       "ieml_string" : str(b)},
                                                      {"id" : 3,
                                                       "ieml_string" : str(c)},
                                                      {"id" : 4,
                                                       "ieml_string" : str(d)},
                                                      {"id" : 5,
                                                       "ieml_string" : str(e)},
                                                      {"id" : 6,
                                                       "ieml_string" : str(f)}
                                                      ],
                                           "graph": [
                                               {"substance" : 1,
                                                "attribute" : 2,
                                                "mode" : 6},
                                               {"substance" : 1,
                                                "attribute" : 3,
                                                "mode" : 6},
                                               {"substance" : 2,
                                                "attribute" : 4,
                                                "mode" : 6},
                                               {"substance" : 2,
                                                "attribute" : 5,
                                                "mode" : 6}
                                           ],
                                           "tags" : {
                                               "fr" : "Danser sans les mains",
                                               "en" : "Do the poirier with the hands"
                                           }
                                           }
        request_output = self.sentence_handler.post()
        sentence = get_test_sentence()
        sentence.order()
        self.assertEqual(request_output["ieml"], str(sentence))

    def test_sentence_error_reporting(self):
        a, b, c, d, e, f = tuple(get_words_list())
        self.sentence_handler.json_data = {"validation_type" : 1,
                                           "nodes" : [{"id" : 1,
                                                       "ieml_string" : str(a)},
                                                      {"id" : 2,
                                                       "ieml_string" : str(b)},
                                                      {"id" : 3,
                                                       "ieml_string" : str(c)},
                                                      {"id" : 4,
                                                       "ieml_string" : str(d)},
                                                      {"id" : 5,
                                                       "ieml_string" : str(e)},
                                                      {"id" : 6,
                                                       "ieml_string" : str(f)}
                                                      ],
                                           "graph": [
                                               {"substance" : 1,
                                                "attribute" : 2,
                                                "mode" : 6},
                                               {"substance" : 1,
                                                "attribute" : 3,
                                                "mode" : 6},
                                               {"substance" : 2,
                                                "attribute" : 4,
                                                "mode" : 6},
                                               {"substance" : 2,
                                                "attribute" : 5,
                                                "mode" : 6},
                                               {"substance" : 1,
                                                "attribute" : 5,
                                                "mode" : 6}
                                           ],
                                           "tags" : {
                                               "fr" : "Danser sans les mains",
                                               "en" : "Do the poirier with the hands"
                                           }
                                           }
        request_output = self.sentence_handler.post()
        self.assertIn("ERROR_CODE", request_output)
        self.assertEqual(request_output["ERROR_CODE"], 2)


class TestTextDecomposition(unittest.TestCase):
    # TODO : Fix this unittest
    def setUp(self):
        self.text_handler = TextDecompositionHandler()
        self.text_handler.do_request_parsing = MagicMock(name="do_request_parsing")

        with open("../data/example_supersentence.txt") as ss:
            self.text_handler.args = {"data": "{/%s/}" % ss}

        self.text_handler.db_connector_term = Mock()
        self.text_handler.db_connector_term = Mock()

    def test_text_decomposition(self):
        """Tests the whole word validation code block without the request handling"""

        request_output = self.text_handler.post()

