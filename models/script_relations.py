from models.base_queries import DBConnector
from models.constants import SCRIPTS_COLLECTION, ROOT_PARADIGM_TYPE, SINGULAR_SEQUENCE_TYPE, PARADIGM_TYPE
from models.exceptions import InvalidScript, NotAParadigm, InvalidDbState, RootParadigmIntersection, \
    ParadigmAlreadyExist, RootParadigmMissing, NotARootParadigm, SingularSequenceAlreadyExist, NotASingularSequence, \
    DBException
from pymongo.errors import DuplicateKeyError
from ieml.script import Script
from ieml.parsing.script import ScriptParser


class ScriptConnector(DBConnector):
    def __init__(self):
        super().__init__()
        self.scripts = self.db_term[SCRIPTS_COLLECTION]
        self.script_parser = ScriptParser()

    def _get_script(self, ieml):
        return self.scripts.find_one({"_id": ieml})

    def db_singular_sequences(self, paradigm=None):
        if paradigm:
            return self.scripts.find({'_id': paradigm})['SINGULAR_SEQUENCES']

        result = list((self.scripts.aggregate([
            {'$match': {'TYPE': ROOT_PARADIGM_TYPE}},
            {'$unwind': '$SINGULAR_SEQUENCES'},
            {'$group': {'_id': 0, 'RESULT': {'$push': '$SINGULAR_SEQUENCES'}}},
        ])))

        if result:
            return result[0]['RESULT']
        else:
            return []

    def get_relations(self, script, relation=None):
        if isinstance(script, str):
            script_str = script
        elif isinstance(script, Script):
            script_str = str(script)
        else:
            raise InvalidScript()

        if relation:
            return self._get_script(script_str)['RELATIONS'][relation]
        else:
            return self._get_script(script_str)['RELATIONS']

    def save_script(self, script, root=False):
        if isinstance(script, Script):
            script_ast = script
        elif isinstance(script, str):
            script_ast = self.script_parser.parse(script)
        else:
            raise InvalidScript()

        if script_ast.paradigm:
            self.save_paradigm(script_ast, root=root)
        else:
            self._save_singular_sequence(script_ast)

    def save_paradigm(self, script, root=False):
        """
        Save a paradigm to the database.

        :param script: the string of the script or an Script object.
        :param root: true if the paradigm is a root paradigm
        :return: None
        """
        if isinstance(script, Script):
            script_ast = script
        elif isinstance(script, str):
            script_ast = self.script_parser.parse(script)
        else:
            raise InvalidScript()

        if not script_ast.paradigm:
            raise NotAParadigm()

        if root:
            self._save_root_paradigm(script_ast)
        else:
            self._save_paradigm(script_ast)

    def _save_singular_sequence(self, script_ast):
        """

        :param script_ast:
        :return:
        """
        # check if a singular sequence
        if script_ast.cardinal != 1:
            raise NotASingularSequence()

        # check if already exist
        if self._get_script(str(script_ast)):
            raise SingularSequenceAlreadyExist()

        # get all the singular sequence of the db to see if the singular sequence can be created
        if str(script_ast) not in self.db_singular_sequences():
            raise RootParadigmMissing()

        # save the singular sequence
        insertion = {
            '_id': str(script_ast),
            'TYPE': SINGULAR_SEQUENCE_TYPE,
            'ROOT': self._compute_root(script_ast),
            'RELATIONS': {},
            'SINGULAR_SEQUENCES': [str(script_ast)]
        }
        self.scripts.insert(insertion)

    def _save_root_paradigm(self, script_ast):
        """
         Save a root paradigm :
            - save the root paradigm
            - save all the singular sequence

        :param script_ast: the paradigm ast
        :return: None
        """
        # defensive check

        # check if paradigm already saved
        if self._get_script(str(script_ast)):
            raise ParadigmAlreadyExist()

        # get all the singular sequence of the db to avoid intersection
        if set.intersection(set(str(seq) for seq in script_ast.singular_sequences), self.db_singular_sequences()):
            raise RootParadigmIntersection()

        # save the root paradigm
        insertion = {
            '_id': str(script_ast),
            'TYPE': ROOT_PARADIGM_TYPE,
            'ROOT': str(script_ast),
            'RELATIONS': {},
            'SINGULAR_SEQUENCES': [str(seq) for seq in script_ast.singular_sequences]
        }
        self.scripts.insert(insertion)

    def _save_paradigm(self, script_ast):
        # defensive check
        if self._get_script(str(script_ast)):
            raise ParadigmAlreadyExist()

        # get all the singular sequence of the db to check if we can create the paradigm
        if not set(str(seq) for seq in script_ast.singular_sequences).issubset(self.db_singular_sequences()):
            raise RootParadigmMissing()

        insertion = {
            '_id': str(script_ast),
            'TYPE': PARADIGM_TYPE,
            'ROOT': self._compute_root(script_ast),
            'RELATIONS': {},
            'SINGULAR_SEQUENCES': [str(seq) for seq in script_ast.singular_sequences]
        }
        self.scripts.insert(insertion)

    def _compute_root(self, script_ast):
        """Prerequisite: root exist"""
        result = self.scripts.find_one({
            'TYPE': ROOT_PARADIGM_TYPE,
            'SINGULAR_SEQUENCES': {'$all': [str(seq) for seq in script_ast.singular_sequences]}})
        if result is None:
            raise RootParadigmMissing()

        return result['_id']

    def load_old_db(self):
        # Empty the db
        self.scripts.remove({})

        old_connector = self.db_term['terms']
        roots = old_connector.find({'PARADIGM': "1"})
        count = roots.count()
        step = count / 20.0
        inc = 0
        nb_star = 0

        print("\tLoad the root paradigms, %d entries." % count)
        for i, root in enumerate(roots):
            if i - inc > step:
                print('*', end='', flush=True)
                inc = i
                nb_star += 1
            try:
                db.save_script(root['IEML'], root=True)
            except DBException as e:
                print('\nException ' + e.__class__.__name__ + ' for script ' + root['IEML'])
                print('*' * nb_star, end='', flush=True)
        print('\n Done. \n')

        paradigms = old_connector.find({'PARADIGM': "0"})
        count = paradigms.count()
        step = count / 20.0
        inc = 0
        nb_star = 0
        print("\tLoad the paradigms and singular sequence, %d entries." % count)

        for i, paradigm in enumerate(paradigms):
            if i - inc > step:
                print('*', end='', flush=True)
                inc = i
                nb_star += 1
            try:
                self.save_script(paradigm['IEML'])
            except DBException as e:
                print('\nException ' + e.__class__.__name__ + ' for script ' + paradigm['IEML'])
                print('*'*nb_star, end='', flush=True)

if __name__ == '__main__':
    db = ScriptConnector()
    db.load_old_db()
    # db.save_paradigm("M:.-',M:.-',S:.-'B:.-'n.-S:.U:.-',_", root=True)
    # db.save_paradigm("B:.-',M:.-',S:.-'B:.-'n.-S:.U:.-',_")
