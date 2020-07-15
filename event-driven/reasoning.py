import logging
import urllib.parse
from abc import ABC, abstractmethod
import requests

from command_execution_helper import execute_command


class ReasoningHelper(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def reason(self, knowledge_files, query_file=None):
        """
        Derive new knowledge from given knowledge, using semantic reasoning.
        :param knowledge_files: full file path of files containing semantic knowledge: situational facts/logic rules/reasoning theories.
        :param query_file: full file path of a file that contains a logic rule telling what knowledge must be derived by the semantic reasoner.
        :return: the results (a string) outputted by the semantic reasoner.
        """
        pass

    def EYE_output_to_valid_N3_string(self, EYE_output):
        return EYE_output.replace('PREFIX', '@prefix') \
                         .replace('>\r\n', '>.\r\n') \
                         .replace('>\r', '>.\r') \
                         .replace('>\n', '>.\n')


class EYEServerReasoningHelper(ReasoningHelper):
    def __init__(self, EYE_Server_URL):
        super().__init__()
        self._EYE_Server_URL = EYE_Server_URL

    def reason(self, knowledge_files, query_file=None):
        """
        Request an EYE Server over HTTP to do the reasoning.
        EYE Server info: https://github.com/RubenVerborgh/EyeServer
        Dockerized EYE Server info: https://hub.docker.com/r/bdevloed/eyeserver/
        """
        # Settings for the EYE reasoner:
        parameters = {
            # 'nope': 'true'  # No proof explanation (this is actually the default setting)
            'data': knowledge_files
            # data[]: multiple values possible for this URL request string parameter.
        }

        if query_file is None:
            parameters['pass-all'] = 'true'  # Value not necessary actually, see if urllib can handle this.
        else:
            parameters['query'] = query_file  # Output only deduced knowledge that is asked for.

        # Constructing the URL for the request to EYE server:
        # doseq: https://stackoverflow.com/a/18201922/5433896,
        # unquote: EYE server expects normal characters ('/') instead of encoded ones ('%3A').
        url = urllib.parse.unquote(self._EYE_Server_URL + '?' + urllib.parse.urlencode(parameters, doseq=True))

        # Requesting the reasoning operation:
        print('Calling EYE server at {0}...'.format(url))
        response = requests.get(url)
        if response.status_code == 200:  # HTTP OK
            output = self.EYE_output_to_valid_N3_string(response.text)
            self.logger.info(output)
            return output
        else:
            return None


class LocalEYEInstallReasoningHelper(ReasoningHelper):
    def __init__(self, local_EYE_install_path):
        super().__init__()
        self._local_EYE_install_path = local_EYE_install_path

    def reason(self, knowledge_files, query_file=None):
        """
        Execute the semantic reasoning using a locally installed EYE reasoner.
        """
        # Settings for the EYE reasoner:
        options = ["--nope", ]  # No proof explanation (proof explanation is the default setting)
        data = knowledge_files
        if query_file is None:
            query = ['--pass-all']  # Output all deduced knowledge.
        else:
            query = ['--query', query_file]  # Output only deduced knowledge that is asked for.

        # Building the list of arguments (The EYE command expects: eye <options>* <data>* <query>*):
        arguments = options + data + query

        # Executing the reasoner:
        result = execute_command([self._local_EYE_install_path] + arguments)

        # Only keep the triples, not irrelevant info (timing etc.) spit out by the EYE command:
        result_triples = ''
        for line in result.splitlines():
            if len(line) > 0 and not line.startswith('#'):
                result_triples += line + '\n'

        # Return the result to the caller:
        result_triples = self.EYE_output_to_valid_N3_string(result_triples)
        # print(result_triples)  # execute_command prints debug info outputted by EYE, then we can add the triples too.
        self.logger.info(result_triples)
        return result_triples  # so actually an N3 string.
