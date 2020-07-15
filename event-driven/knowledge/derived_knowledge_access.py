import os

import rdflib
from django.conf import settings
from rdflib import Graph

from broker.constants.namespaces import prefix_namespace_bindings


class DerivedKnowledgeAccess:
    def __init__(self, sensor_gateway):
        self.__sensor_gateway = sensor_gateway
        file_name = str(sensor_gateway.id) + '-' + sensor_gateway.name.replace(' ', '_') + '.n3'
        self.__knowledge_file = os.path.join(settings.KNOWLEDGE_DIR, 'derived_knowledge', file_name)

    @staticmethod
    def save_reasoner_output(derived_knowledge_n3: rdflib.Graph):
        file_name = 'reasoner_output' + '.n3'
        knowledge_file = os.path.join(settings.KNOWLEDGE_DIR,
                                      'derived_knowledge/26_04_2019_tryout_merging_anomalies_with_reasoning',
                                      file_name)
        derived_knowledge_n3.serialize(format='n3', destination=knowledge_file, encoding='utf-8')

    def save_derived_knowledge(self, derived_knowledge_n3: rdflib.Graph):
        derived_knowledge_n3.serialize(format='n3', destination=self.__knowledge_file, encoding='utf-8')

    def get_suggested_aggregations_for_property(self, property_url):
        derived_knowledge = Graph()
        derived_knowledge.parse(self.__knowledge_file, format='n3')
        ns_bindings = {
            'dashb': prefix_namespace_bindings['dashb']
        }
        results = derived_knowledge.query("""SELECT DISTINCT ?aggregation_url
                                            WHERE {{
                                                ?aggregation_url dashb:aggregates <{0}> .
                                            }}""".format(property_url),
                                          initNs=ns_bindings)
        aggregation_urls = []
        for result in results:
            aggregation_urls.append(str(result['aggregation_url']))
        return aggregation_urls

    def __query_derived_knowledge(self, query):
        derived_knowledge = Graph()
        derived_knowledge.parse(self.__knowledge_file, format='n3')
        derived_knowledge.parse(os.path.join(settings.KNOWLEDGE_DIR, 'downloaded_knowledge', 'm3lite.n3'), format="n3")
        return derived_knowledge.query(query, initNs=prefix_namespace_bindings)
