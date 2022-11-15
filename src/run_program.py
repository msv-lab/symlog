from subprocess import run, DEVNULL, CalledProcessError
from tempfile import TemporaryDirectory, NamedTemporaryFile
import utils


def run_program(program, relations):
    with NamedTemporaryFile() as datalog_script:
        datalog_script.write(utils.pprint(program).encode())
        datalog_script.flush()
        with TemporaryDirectory() as input_directory:
            utils.write_relations(input_directory, relations)
            with TemporaryDirectory() as output_directory:
                cmd = [
                    "souffle",
                    "-F", input_directory,
                    "-D", output_directory,
                    datalog_script.name
                ]
                try:
                    run(cmd, check=True, stdout=DEVNULL)#, stderr=DEVNULL)
                except CalledProcessError:
                    print("----- error while solving: ----")
                    print(utils.pprint(program))
                    print("---- on -----------------------")
                    print(relations)
                    exit(1)
                return utils.load_relations(output_directory)