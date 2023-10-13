import symlog.type_analyser
import symlog.syntax_checker
import symlog.program_manager
import symlog.symbolic_executor
import symlog.parser
import symlog.transformer
import symlog.repairer
import logging


class Environment:
    TypeAnalyserClass = symlog.type_analyser.TypeAnalyser
    SyntaxCheckerClass = symlog.syntax_checker.SyntaxChecker
    ProgramManagerClass = symlog.program_manager.ProgramManager
    SymbolicExecutorClass = symlog.symbolic_executor.SymbolicExecutor
    ParserClass = symlog.parser.Parser
    TransformerClass = symlog.transformer.Transformer
    RepairerClass = symlog.repairer.Repairer

    def __init__(self) -> None:
        self._type_analyser = self.TypeAnalyserClass(self)
        self._syntax_checker = self.SyntaxCheckerClass(self)
        self._program_manager = self.ProgramManagerClass(self)
        self._transformer = self.TransformerClass(self)
        self._parser = self.ParserClass(self)
        self._symbolic_executor = self.SymbolicExecutorClass(self)
        self._repairer = self.RepairerClass(self)

    @property
    def type_analyser(self):
        return self._type_analyser

    @property
    def syntax_checker(self):
        return self._syntax_checker

    @property
    def program_manager(self):
        return self._program_manager

    @property
    def symbolic_executor(self):
        return self._symbolic_executor

    @property
    def parser(self):
        return self._parser

    @property
    def transformer(self):
        return self._transformer

    @property
    def repairer(self):
        return self._repairer

    def __enter__(self):
        """Entering a Context"""
        push_env(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove environment from global stack."""
        pop_env()


#### GLOBAL ENVIRONMENTS STACKS ####
ENVIRONMENTS_STACK = []


def get_env():
    """Returns the Environment at the head of the stack."""
    return ENVIRONMENTS_STACK[-1]


def push_env(env=None):
    """Push a env in the stack. If env is None, a new Environment is created."""
    if env is None:
        env = Environment()
    ENVIRONMENTS_STACK.append(env)


def pop_env():
    """Pop an env from the stack."""
    return ENVIRONMENTS_STACK.pop()


def reset_env():
    """Destroys and recreate the head environment."""
    pop_env()
    push_env()
    return get_env()


# Create the default environment
push_env()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
