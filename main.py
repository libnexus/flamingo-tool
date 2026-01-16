from flamingo.core.kernel import FlamingoKernel
from flamingo.core.user import User
from flamingo.interface.shell import run_shell


def setup(kernel: FlamingoKernel):
    kernel.current_user = kernel.users["flamingo"] = User("flamingo", kernel.system_vars.child("flamingo"))


if __name__ == '__main__':
    run_shell(FlamingoKernel())
