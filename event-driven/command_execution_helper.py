from subprocess import check_output, CalledProcessError


def execute_command(command: list):
    """
    Execute a command on the underlying operating system.
    :param command: a list of parts that the command consists of. This is safer, because then we can leave it up to the
    library we call for executing the command, to also compose all parts of the command first into one command string
    that the specific OS understands (including ""-escaping of file paths that contain spaces etc).
    :return: the output that the command, as as string.
    :raises: subprocess.CalledProcessError in case of problems during command execution.
    """

    # Execute the command string (will throw CalledProcessError in case of command execution problems):
    try:
        command_output = check_output(command)
        return str(command_output, 'utf-8')  # command_output is a byte string: b'somethingsomething'.
    except CalledProcessError as err:
        if command[0].endswith("eye.cmd"):  # Strangely enough, the EYE reasoner can output error code 1 but still produce fine results.
            return str(err.output, 'utf-8')
        else:
            print(f"Executing the command failed with the return code {err.returncode} and the following output:")
            print(str(err.output, 'utf-8'))
            raise
