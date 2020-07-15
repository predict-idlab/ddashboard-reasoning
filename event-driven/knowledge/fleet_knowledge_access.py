import os

from django.conf import settings
from rdflib import Graph

from broker.constants.namespaces import prefix_namespace_bindings
from broker.utilities.rdflib_helper import RdflibHelper


class FleetKnowledgeAccess:
    def __init__(self, sensor_gateway):
        if sensor_gateway is not None:
            # Variables:
            self.__sensor_gateway = sensor_gateway
            self.__knowledge_file = self.get_fleet_knowledge_file()

        # Dependencies:
        self._rdflib_helper = RdflibHelper()

    def get_fleet_knowledge_file(self):
        fleet_knowledge_folder = os.path.join(settings.KNOWLEDGE_DIR, 'fleet_knowledge')
        knowledge_file_name = str(self.__sensor_gateway.id) + '-' + self.__sensor_gateway.name.replace(' ', '_') + '.n3'
        return os.path.join(fleet_knowledge_folder, knowledge_file_name)

    def save_fleet_knowledge(self, knowledge_graph):
        self._rdflib_helper.bind_all_namespaces(knowledge_graph)
        knowledge_graph.serialize(destination=self.__knowledge_file, format='n3')

    def __query_fleet_knowledge(self, query):
        fleet_knowledge = Graph()
        fleet_knowledge.parse(self.__knowledge_file, format='n3')
        fleet_knowledge.parse(os.path.join(settings.KNOWLEDGE_DIR, 'downloaded_knowledge', 'm3lite.n3'), format="n3")
        return fleet_knowledge.query(query, initNs=prefix_namespace_bindings)

    def get_aggregation_info(self, aggregation_url):
        results = self.__query_fleet_knowledge("""SELECT ?id ?name
                                                   WHERE {{
                                                       <{0}> dcterms:identifier ?id ;
                                                           rdfs:label ?name .
                                                   }}""".format(aggregation_url))
        aggregation = None
        for result in results:
            aggregation = {
                'id': str(result['id']),
                'name': str(result['name']),
                'rootUrl': aggregation_url
            }
        return aggregation

    def get_aggregations(self):
        fleet_knowledge = Graph()
        knowledge_file = os.path.join(settings.KNOWLEDGE_DIR, 'facts', 'aggregations.ttl')
        fleet_knowledge.parse(knowledge_file, format='n3')

        query = """SELECT ?processor ?type ?name
                    WHERE {{
                        ?processor a ?type ;
                            rdfs:label ?name .
                    }}
                """

        results = fleet_knowledge.query(query, initNs=prefix_namespace_bindings)
        aggregations = []
        for result in results:
            aggregations.append({
                'processor': str(result['processor']),
                'type': str(result['type']),
                'name': str(result['name'])
            })
        return aggregations

    def get_properties_in_subsystems(self, subsystems):
        sensor_properties = []
        sensors = []

        def get_only_common_properties_in_all_systems(sensor_properties, subsystem_urls):
            # common_sensor_properties = {}
            common_sensor_properties = []
            for property in sensor_properties:
                if 1 < len(subsystem_urls) == len(property.get('observationsUrls')):
                    common_sensor_properties.append(property)
                    # if property.get('label') not in common_sensor_properties.keys():
                    #    common_sensor_properties[property.get('label')] = property.get('observationsUrls')
                elif len(subsystem_urls) == 1 and len(property.get('observationsUrls')) >= 1:
                    common_sensor_properties.append(property)
                    # if property.get('label') not in common_sensor_properties.keys():
                    #    common_sensor_properties[property.get('label')] = property.get('observationsUrls')

            return common_sensor_properties

        i = 0
        for subsystem_url in subsystems:
            query_all_properties = """SELECT *
                WHERE {{
                ?sensor_url a sosa:Sensor ;
                    sosa:observes ?observationsUrl ;
                    ssn-ext:subSystemOf* <{0}> .
                ?observationsUrl a sosa:ObservableProperty;
                    rdf:type ?property_type ;
                    dcterms:identifier ?id ;
                    rdfs:label ?name .
                ?property_type rdfs:label ?label
                }}""".format(subsystem_url)

            results = self.__query_fleet_knowledge(query_all_properties)

            # only if the query returns results, it means the system is a sensor and has sensor-properties
            if len(results) > 0:
                sensors.append(subsystem_url)

            for result in results:
                temp = {}
                if len(sensor_properties) != 0:
                    for sensor_property in sensor_properties:
                        # if sensor property kind does already exist in the sensor property collection
                        if result['id'] == sensor_property['id']:
                            sensor_property['observationsUrls'].append(
                                result['observationsUrl']
                            )
                            break
                        # if sensor property kind does not yet exist in the sensor property collection:
                        # add to collection
                        else:
                            temp.update({
                                'id': result['id'],
                                'name': result['name'],
                                'observationsUrls': [result['observationsUrl']]
                            })
                else:
                    sensor_properties.append({
                        'id': result['id'],
                        'name': result['name'],
                        'observationsUrls': [result['observationsUrl']]
                    })
                    i += 1  # only if there's been added a new sensor property to the array, the index increases

                if len(temp) > 1:
                    sensor_properties.append(temp)
                    i += 1  # only if there's been added a new sensor property to the array, the index increases

        unique_properties = get_only_common_properties_in_all_systems(sensor_properties, sensors)
        return unique_properties

    def get_hierarchy(self):
        query_all_systems = """SELECT *
                                WHERE {
                                    ?url a ssn:System .
                                    ?url rdfs:label ?name .
                                    OPTIONAL { ?url ssn-ext:subSystemOf ?subsystem }
                                }"""
        systems = []
        for system in self.__query_fleet_knowledge(query_all_systems):
            print(system)
            systems.append({
                "value": system['url'],
                "text": system['name'],
                "checked": False,
                "parent": system['subsystem'],
                "children": []
            })

        def is_child(item, parent):
            if parent is None and item['parent'] is None:
                return True
            elif parent is not None:
                return item['parent'] == parent['value']
            else:
                return False

        def build_tree(systems, parent=None):
            tree = []
            children = [system for system in systems if is_child(system, parent)]

            if children:
                if parent is None:
                    tree = children
                else:
                    parent['children'] = children
                for child in children:
                    build_tree(systems, child)

            return tree

        hierarchy_tree = build_tree(systems)
        print(hierarchy_tree)

        return hierarchy_tree

    def save_derived_knowledge(self, derived_knowledge_graph):
        derived_knowledge_graph.serialize(format='n3', destination=self.__knowledge_file)
