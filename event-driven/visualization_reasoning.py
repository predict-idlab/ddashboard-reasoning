from os import makedirs, remove
from os.path import exists, join
from random import randint
from time import time

from rdflib import Graph

from reasoning import ReasoningHelper

prefix_namespace_bindings = {
    'sosa': 'http://www.w3.org/ns/sosa/',
    'ssn': 'http://www.w3.org/ns/ssn/',
    'ssn-ext': 'http://dynamicdashboard.ilabt.imec.be/broker/ontologies/ssn-extension/',
    'dashb': 'http://dynamicdashboard.ilabt.imec.be/broker/ontologies/dashboard/',
    'dcterms': 'http://purl.org/dc/terms/',
    'm3lite': 'http://purl.org/iot/vocab/m3-lite#',
    'rdfs': "http://www.w3.org/2000/01/rdf-schema#",
    'qu': 'http://purl.org/NET/ssnx/qu/qu#',
    "metrics": "http://dynamicdashboard.ilabt.imec.be/broker/ontologies/metrics#",
    "time": "http://www.w3.org/2006/time#",
    "folio": "http://IBCNServices.github.io/Folio-Ontology/Folio.owl#",
    "renson": "http://renson.be/broker/visualizations/roomtype#"
}


class VisualizationSuggestionsReasoner:
    def __init__(self, 
                 knowledge_folder: str,
                 reasoning_helper: ReasoningHelper):
        self._knowledge_folder = knowledge_folder
        self._reasoning_helper = reasoning_helper

    def _run_reasoner(self,
                      input_graph,
                      input_metadata_graph,
                      knowledge_files,
                      query=None,
                      query_file=None,
                      remove_temporary_files_afterwards=True):
        # Create a folder for some temporary files:
        temp_dir = join(self._knowledge_folder, 'temporary_knowledge')
        if not exists(temp_dir):
            makedirs(temp_dir)

        # Create some file name modifier that will make the temporary files, created below, unique (no overwriting):
        file_modifier = "{}-{}".format(int(round(time() * 1000)), randint(0, 9999))

        # Create a temporary file for the inputted sensor properties to visualize:
        input_file = join(temp_dir, 'input-{}.ttl'.format(file_modifier))
        input_graph.serialize(format='n3', destination=input_file, encoding='utf-8')

        # Fetch the metadata of the given sensor property:
        temp_input_metadata_path = join(temp_dir, 'input-metadata-{}.ttl'.format(file_modifier))
        input_metadata_graph.serialize(format='n3', destination=temp_input_metadata_path, encoding='utf-8',
                                       context=prefix_namespace_bindings)

        # Create a temporary query file, to tell the reasoner what the desired output is:
        if query_file is None:
            temp_query_file = join(temp_dir, 'query-{}.n3'.format(file_modifier))
            with open(temp_query_file, 'w+') as f:
                f.write(query)

        # Run the EYE reasoner:
        knowledge_files.append(input_file)
        knowledge_files.append(temp_input_metadata_path)

        start_time = time()
        derived_knowledge = self._reasoning_helper.reason(knowledge_files=knowledge_files,
                                                          query_file=temp_query_file if query_file is None else query_file)
        end_time = time()
        reasoning_time = end_time - start_time

        # Remove temporary files:
        if remove_temporary_files_afterwards:
            remove(input_file)
            remove(temp_input_metadata_path)
            if query_file is None:
                remove(temp_query_file)

        # Return the reasoner output as a graph:
        graph = Graph().parse(data=derived_knowledge, format='n3')
        return graph, reasoning_time
    
    
    def suggest_visualizations_for_anomaly(self, input_graph, input_metadata_graph, remove_temporary_files_afterwards=True):
        # Combine all knowledge and logic rules:
        knowledge_files = [
            # the base class will add a temporary file containing input_graph
            # the base class will add the input_metadata_file or a temporary graph containing input_metadata_graph
            join(self._knowledge_folder, 'downloaded_knowledge', 'Folio.ttl'),
            join(self._knowledge_folder, 'facts', 'metrics.ttl'),
            join(self._knowledge_folder, 'facts', 'visualizations', 'anomaly_visualizations.ttl'),
            join(self._knowledge_folder, 'facts', 'visualizations', 'historical_data_visualizations.ttl'),
            join(self._knowledge_folder, 'theory', 'rdfs-subClassOf.n3'),
            join(self._knowledge_folder, 'rules', 'visualize_anomalies-all_options.n3'),
            join(self._knowledge_folder, 'rules', 'visualizations.n3'),
            join(self._knowledge_folder, 'ontologies', 'dashboard.owl')
        ]
    
        # Create a temporary query file, to tell the reasoner what the desired output is:
        query_file = join(self._knowledge_folder, 'queries', 'anomaly_visualization_suggestions.n3')
    
        # Run the EYE reasoner:
        return self._run_reasoner(input_graph, input_metadata_graph, knowledge_files,
                                  query=None,
                                  query_file=query_file,
                                  remove_temporary_files_afterwards=remove_temporary_files_afterwards)
