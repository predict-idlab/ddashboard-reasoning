import os
import platform

from rdflib import Graph
from rdflib.util import guess_format
import numpy as np

from reasoning import EYEServerReasoningHelper, LocalEYEInstallReasoningHelper
from visualization_reasoning import VisualizationSuggestionsReasoner

KNOWLEDGE_DIR = r".\knowledge"
REASON_WITH_EYE_SERVER = False
EYE_SERVER_URL = 'http://eye-server:8000'
LOCAL_EYE_REASONER_PATH = r"C:\Program Files\eye\bin\eye.cmd" if platform.system() == 'Windows' else '/opt/eye/bin/eye.sh'
ANOMALY_METADATA_FOLDER = r".\anomaly-metadata"
NUM_EXECUTIONS_TO_CALCULATE_TIMINGS = 5


def find_anomaly_url(anomaly_metadata_graph: Graph, is_merged_anomaly=False):
    anomaly_type = 'folio:MergedAnomaly' if is_merged_anomaly else 'folio:Anomaly'
    query = f"""
    SELECT ?anomaly
    WHERE
    {{
        ?anomaly a { anomaly_type } .
    }}
    """
    results = anomaly_metadata_graph.query(query,
                                           initNs={'folio': 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#'})
    anomaly_url = str([result['anomaly'] for result in results][0])
    return anomaly_url


def create_anomaly_investigation_tab(anomaly_url, anomaly_metadata_graph):
    if REASON_WITH_EYE_SERVER:
        reasoning_helper = EYEServerReasoningHelper(EYE_SERVER_URL)
    else:
        reasoning_helper = LocalEYEInstallReasoningHelper(LOCAL_EYE_REASONER_PATH)
    reasoner = VisualizationSuggestionsReasoner(KNOWLEDGE_DIR, reasoning_helper)

    input_n3 = f"""
        @prefix dashb: <http://dynamicdashboard.ilabt.imec.be/broker/ontologies/dashboard#> .

        _:tab dashb:investigatedAnomaly <{anomaly_url}> .
        """
    input_graph = Graph()
    input_graph.parse(data=input_n3, format='n3')

    reasoning_output, reasoning_time = reasoner.suggest_visualizations_for_anomaly(input_graph, anomaly_metadata_graph,
                                                                                   remove_temporary_files_afterwards=False)
    print(f"==> The semantic reasoning has finished (in {reasoning_time} s). The output is:\r\n")
    print(reasoning_output.serialize(format='n3').decode('utf-8'))

    return reasoning_output, reasoning_time


def test_create_anomaly_investigation_tab(anomaly_metadata_file, is_merged_anomaly=False):
    anomaly_metadata_file_path = os.path.join(ANOMALY_METADATA_FOLDER, anomaly_metadata_file)
    anomaly_metadata_graph = Graph()
    anomaly_metadata_graph.parse(source=anomaly_metadata_file_path, format='n3')

    anomaly_url = find_anomaly_url(anomaly_metadata_graph, is_merged_anomaly)

    reasoning_output, reasoning_time = create_anomaly_investigation_tab(anomaly_url, anomaly_metadata_graph)
    return reasoning_output, reasoning_time


def time_test_create_anomaly_investigation_tab(anomaly_metadata_file, number_of_executions=5, is_merged_anomaly=False):
    reasoning_times = []
    for _ in range(number_of_executions):
        reasoning_output, reasoning_time = test_create_anomaly_investigation_tab(anomaly_metadata_file, is_merged_anomaly)
        reasoning_times.append(reasoning_time)
    return reasoning_times


def format_reasoning_times(reasoning_times):
    mean_std = f"{np.mean(reasoning_times)} (+- {np.std(reasoning_times)} std)"
    return ' | '.join([str(t) for t in reasoning_times]) + ' | ' + mean_std

# Renson:
# Testing on the anomalies produced by each detector:
reasoning_times_table = []
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-simple-uad-anomaly.n3',
                                                                        NUM_EXECUTIONS_TO_CALCULATE_TIMINGS))
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-simple-room-type-classifier-anomaly.n3',
                                                                        NUM_EXECUTIONS_TO_CALCULATE_TIMINGS))
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-simple-semantic-fault-detection-anomaly.n3',
                                                                        NUM_EXECUTIONS_TO_CALCULATE_TIMINGS))
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-simple-kpd-anomaly.n3',
                                                                        NUM_EXECUTIONS_TO_CALCULATE_TIMINGS))
# Missing: the 2 rule miners.
# Testing anomalies that were adapted with user feedback:
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-relabeled-anomaly.n3',
                                                                        NUM_EXECUTIONS_TO_CALCULATE_TIMINGS))
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-merged-anomaly.n3',
                                                                        number_of_executions=NUM_EXECUTIONS_TO_CALCULATE_TIMINGS,
                                                                        is_merged_anomaly=True))
reasoning_times_table.append(time_test_create_anomaly_investigation_tab('semantic-relabeled-merged-anomaly.n3',
                                                                        number_of_executions=NUM_EXECUTIONS_TO_CALCULATE_TIMINGS,
                                                                        is_merged_anomaly=True))
for reasoning_times in reasoning_times_table:
    print(format_reasoning_times(reasoning_times))
