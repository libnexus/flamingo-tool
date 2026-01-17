from flamingo.core.kernel import FlamingoKernel
from flamingo.interface.shell import run_shell
import sys

if __name__ == '__main__':
    run_shell(FlamingoKernel(), sys.argv[1:])
