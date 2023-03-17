from core.utils import convert_relations, inv_convert_relations, read_file
import core.souffle as souffle
from core.transform_to_meta_program import transform_program
from core.ast import SymConstant


class Symlog:
    """ 
    Args:
        program_path (str): The path to the Souffle program file.
        database_path (Optional[str]): The path to the Souffle database file, default is None.

    Attributes:
        program (souffle.Program): The Souffle program object.
        input_facts (Dict[str, List[Dict[str, Union[str, int, float]]]]): A dictionary of input facts for the Souffle program.

    Methods:
        transform(): Transforms the input facts for the Souffle program.
        run(): Runs the transformed Souffle program and returns the output.

    Raises:
        FileNotFoundError: If either the program_path or database_path does not exist.

    Notes:
        This class requires the Souffle library to be installed in the system.

    Example:
        >>> symlog = Symlog("path/to/souffle/program.dl", "path/to/souffle/database/facts")
        >>> symlog.run()
        {'relation1': [(value1, value2), (value3, value4)], 'relation2': [(value5), (value6, value7)]}
    """

    def __init__(self, program_path, database_path=None) -> None:
        self.program = souffle.parse(read_file(program_path))
        self.input_facts = convert_relations(souffle.load_relations(database_path)) if not database_path is None else list()
        # reset id iterator for symbolic constants
        SymConstant.reset_id_iter()

    def transform(self):
        self.input_facts = inv_convert_relations(self.input_facts)
        return transform_program(self.program, self.input_facts)

    def run(self):
        return souffle.run_program(self.transform(), self.input_facts)
