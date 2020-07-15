from os import sep
from os.path import dirname, basename, relpath, normpath
from datetime import datetime
import pytz
import urllib.parse
from functools import lru_cache

from django.urls import reverse
from django.conf import settings
from json import dumps, loads
from SPARQLWrapper import SPARQLWrapper, SPARQLWrapper2, JSON, TURTLE, JSONLD, N3
from kafka import KafkaProducer
from rdflib import Graph
from kafka.errors import KafkaError

from .anomalies import UnknownPatternAnomaly, KnownPatternAnomaly, RelabeledAnomaly, MergedAnomaly, \
    UnknownRoomAnomaly, TrackIssueAnomaly

RELABEL_DESCRIPTION = 'Please relabel.'


def query_stardog_db(stardog_url, query, method='GET'):
    """
    Query a Stardog database, return the result as a RDFLib graph.
    """
    print("\nQuerying Stardog on", stardog_url)
    # https://stardog.docs.apiary.io/#reference/core-api
    try:
        sparql = SPARQLWrapper(stardog_url)
        sparql.setCredentials(settings.STARDOG_USER, settings.STARDOG_PASSWORD)
        sparql.setMethod(method)
        sparql.setReturnFormat(TURTLE)
        sparql.setQuery(query)
        results_string = sparql.query().convert()
        results_graph = Graph()
        results_graph.parse(data=results_string, format="n3")
        print("Querying Stardog - SUCCESS")
        return results_string, results_graph
    except Exception as e:
        print("Querying Stardog failed:", e.__class__.__name__, e)


def query_stardog_db_return_object(stardog_url, query, method='GET'):
    """
    Query a Stardog database, return the result as an iterable object.
    """
    print("\nQuerying Stardog on", stardog_url)
    # https://stardog.docs.apiary.io/#reference/core-api
    try:
        sparql = SPARQLWrapper2(stardog_url)
        sparql.setCredentials(settings.STARDOG_USER, settings.STARDOG_PASSWORD)
        sparql.setMethod(method)
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        results = sparql.query().convert()
        print("Querying Stardog - SUCCESS")
        return results.bindings
    except Exception as e:
        print("Querying Stardog failed:", e.__class__.__name__, e)


def n3_to_jsonld(n3_string, context=None):
    graph = Graph().parse(data=n3_string, format='n3')
    return loads(graph.serialize(format='json-ld', context=context, encoding='utf-8'))


class ExternalKnowledgeAccess:
    def __init__(self, sensor_gateway):
        self.__sensor_gateway = sensor_gateway

    def get_URL_for_local_knowledge_file(self, local_knowledge_file):
        """
        Make a local knowledge file available for external web services.
        The local knowledge file can be in any subfolder of the knowledge folder.
        Using Django's URL reversing: https://docs.djangoproject.com/en/2.0/ref/urlresolvers/#reverse
        Note: for now, this function is only needed so EYE Server can access files on the broker.
        We assume here that either:
         - broker and EYE server are dockerized, either in production or on localhost for development,
         and can contact each other through the virtual network between both docker containers,
         - or the broker is running on "pure" localhost, and the EYE Server too, either in a container or on localhost too,
         so it can contact the broker on "localhost".
        """
        # remove path components up to knowledge dir, then split components
        parts = normpath(relpath(local_knowledge_file, settings.KNOWLEDGE_DIR)).split(sep)
        partial_url = reverse('knowledge', args=['/'.join(parts[:-1]), parts[-1]], current_app='broker')
        host = settings.ROOT_URL.rstrip('/')
        url = host + partial_url.replace('/broker',
                                         '')  # possibly .split('/broker')[1] instead, we have encountered a bug with this before
        return url

    #  TODO: revise code!!
    def get_anomaly_by_id(self, anomaly_id):
        # Stardog communication
        try:
            print("\nQuerying Stardog on", self.__sensor_gateway.stardog_url_for_anomalies)
            # https://stardog.docs.apiary.io/#reference/core-api
            sparql = SPARQLWrapper2(self.__sensor_gateway.stardog_url_for_anomalies)
            sparql.setCredentials(settings.STARDOG_USER, settings.STARDOG_PASSWORD)
            sparql.setMethod("GET")
            sparql.setReturnFormat(JSON)

            if "merged" in anomaly_id:
                sparql_query = """SELECT *
                                    WHERE{{
                                        <{0}> <http://www.w3.org/ns/sosa/resultTime> ?resultTime ;
                                        <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?anomalyType ;
                                        <http://www.w3.org/ns/sosa/usedProcedure> ?usedProcedure ;
                                        <http://purl.org/dc/terms/description> ?description ;
                                        <http://IBCNServices.github.io/Folio-Ontology/Folio.owl#hasSubAnomaly> ?hasSubAnomaly ;
                                    }}""".format(anomaly_id)
                sparql.setQuery(sparql_query)
                results = sparql.query().convert()

                anomaly = {}
                mergedAnomalies = []
                sensor = set()
                property = set()
                fromarr = []
                toarr = []

                for result in results.bindings:
                    anomaly = {
                        'type': str(result['anomalyType'].value),
                        'description': str(result['description'].value),
                        'resultTime': str(result['resultTime'].value)
                    }

                    subanomaly = self.get_anomaly_by_id(result["hasSubAnomaly"].value)
                    mergedAnomalies.append(subanomaly)

                    sensor.add(subanomaly["sensor"][0])
                    property.add(subanomaly["property"][0])
                    fromarr.append(subanomaly["from"][0])
                    toarr.append(subanomaly["to"][0])

                anomaly["id"] = anomaly_id
                anomaly["sensor"] = list(sensor)
                anomaly["property"] = list(property)
                anomaly["from"] = [min(fromarr)] if len(fromarr) > 0 else []
                anomaly["to"] = [max(toarr)] if len(toarr) > 0 else []
                anomaly["isChecked"] = False
                anomaly["canEdit"] = False
                anomaly["mergedAnomalies"] = mergedAnomalies

                return anomaly
            else:
                sparql_query = """PREFIX folio: <http://IBCNServices.github.io/Folio-Ontology/Folio.owl#>
                                  SELECT *
                                  WHERE{{
                                        <{0}> <http://www.w3.org/ns/sosa/resultTime> ?resultTime ;
                                            <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?anomalyType ;
                                            <http://www.w3.org/ns/ssn/wasOriginatedBy> ?metadata ;
                                            <http://www.w3.org/ns/sosa/usedProcedure> ?usedProcedure ;
                                            <http://purl.org/dc/terms/description> ?description ;
                                            <https://idlab-iot.tengu.io/api/v1/vocabulary/metricId> ?metricId ;
                                            <https://idlab-iot.tengu.io/api/v1/vocabulary/thingId> ?thingId .
                                        
                                        OPTIONAL {{
                                            <{0}> folio:hasCauseDescription ?explanation .
                                        }}
                                  }}""".format(anomaly_id)
                sparql.setQuery(sparql_query)
                results = sparql.query().convert()
                anomaly = None
                for result in results.bindings:
                    print(result)
                    metadata = str(result['metadata'].value).replace('http://example.com/stimulus/', '').split('/')
                    anomaly = {
                        'id': anomaly_id,
                        'type': str(result['anomalyType'].value),
                        'description': str(result['description'].value),
                        'sensor': [str(result['thingId'].value)],
                        'property': [str(result['metricId'].value).replace('_', '.')],
                        'from': [int(metadata[2])],
                        'to': [int(metadata[3])],
                        'resultTime': str(result['resultTime'].value),
                        'isChecked': False,
                        'canEdit': False
                    }
                    if 'explanation' in result.keys():
                        anomaly['explanation'] = str(result['explanation'].value)
                return anomaly
        except Exception as e:
            print("Querying Stardog failed:", e.__class__.__name__, e)

    def write_relabeled_anomaly_to_kafka(self, relabeled_anomaly, sensor_gateway):
        a = RelabeledAnomaly()
        types = a.atypes + list(set(relabeled_anomaly["type"]) - set(a.atypes))
        types = [t.split('#')[1] for t in types]

        parts = []
        sub_anomalies = []
        if "mergedAnomalies" in relabeled_anomaly and relabeled_anomaly["mergedAnomalies"] is not None:
            for _a in relabeled_anomaly["mergedAnomalies"]:
                sub_anomalies.append({"id": _a["id"]})
        else:
            parts = [
                {
                    "thing": relabeled_anomaly["sensor"][0],
                    "property": relabeled_anomaly["property"][0],
                    "from": relabeled_anomaly["from"][0],
                    "to": relabeled_anomaly["to"][0]
                }
            ]

        json_msg = {
            "id": relabeled_anomaly["id"],
            "update": True,
            "generatedBy": relabeled_anomaly["generatedBy"],
            "timestamp": relabeled_anomaly["resultTime"],
            "anomaly": {
                "type": types,
                "description": relabeled_anomaly["description"],
                "parts": parts,
                "subanomalies": sub_anomalies
            }
        }
        relabeled_anomaly["type"] = a.atypes
        if relabeled_anomaly["jsonld"] is not None and "@graph" in relabeled_anomaly["jsonld"]:
            if isinstance(relabeled_anomaly["jsonld"]["@graph"], dict):
                relabeled_anomaly["jsonld"]["@graph"]["@type"] = relabeled_anomaly["type"]
                relabeled_anomaly["jsonld"]["@graph"]["description"] = relabeled_anomaly["description"]
            else:
                for part in relabeled_anomaly["jsonld"]["@graph"]:
                    if part["@id"] == relabeled_anomaly["id"]:
                        part["@type"] = relabeled_anomaly["type"]
                        part["description"] = relabeled_anomaly["description"]
                        break

        if "canEdit" not in relabeled_anomaly:
            relabeled_anomaly["canEdit"] = False
        if "isChecked" not in relabeled_anomaly:
            relabeled_anomaly["isChecked"] = False

        topic_name = sensor_gateway.kafka_topic_anomalies
        self.write_to_kafka(dumps(json_msg), relabeled_anomaly["sensor"][0], topic_name)
        return relabeled_anomaly

    # @lru_cache(maxsize=128)
    def get_distinct_anomaly_descriptions(self):
        # Stardog communication
        try:
            print("\nQuerying Stardog on", self.__sensor_gateway.stardog_url_for_anomalies)
            # https://stardog.docs.apiary.io/#reference/core-api
            sparql = SPARQLWrapper2(self.__sensor_gateway.stardog_url_for_anomalies)
            # sparql = SPARQLWrapper2("http://localhost:5820/dynamic_dashboard/query")
            sparql.setCredentials(settings.STARDOG_USER, settings.STARDOG_PASSWORD)
            sparql.setMethod("GET")
            sparql.setReturnFormat(JSON)
            sparql_query = """SELECT DISTINCT ?description 
                                WHERE {
                                  ?s <http://purl.org/dc/terms/description> ?description .
                                }
                                ORDER BY ASC(?description)"""
            sparql.setQuery(sparql_query)
            results = sparql.query().convert()
            print("Querying Stardog - SUCCESS")
            descriptions = []
            for result in results.bindings:
                descriptions.append(str(result['description'].value))
            return descriptions
        except Exception as e:
            print("Querying Stardog failed:", e.__class__.__name__, e)

    def get_recommended_anomaly_descriptions(self, anomaly):
        # Use set (instead of array or list) to store only distinct values
        # https://stackoverflow.com/questions/12897374/get-unique-values-from-a-list-in-python
        descriptions = set()
        if anomaly['description'] != RELABEL_DESCRIPTION:
            descriptions.add(anomaly['description'])
        if 'mergedAnomalies' in anomaly:
            if anomaly['mergedAnomalies'] is not None:
                for a in anomaly['mergedAnomalies']:
                    if a['description'] != RELABEL_DESCRIPTION:
                        descriptions.add(a['description'])

        return sorted(list(descriptions), key=str.lower)

    def all_same(self, items):
        return all(x == items[0] for x in items)

    #  TODO: revise code
    def merge_anomalies(self, anomalies, sensor_gateway):
        anomaly_types_descriptions = {}
        anomaly_types = set()
        sensor = set()
        property = set()
        fromarr = []
        toarr = []
        subanomalies = []
        generated_hash = ''
        a = MergedAnomaly()

        for anomaly in anomalies:
            if anomaly['type'] in anomaly_types_descriptions:
                anomaly_types_descriptions[anomaly['type']].append(anomaly['description'])
            else:
                anomaly_types_descriptions[anomaly['type']] = [anomaly['description']]
            anomaly_types.add(anomaly['type'])

            sensor.add(anomaly['sensor'][0])
            property.add(anomaly['property'][0])
            fromarr.append(anomaly['from'][0])
            toarr.append(anomaly['to'][0])

            subanomalies.append({"id": anomaly["id"]})
            generated_hash += anomaly['id'] + ';'

        generated_hash = str(hash(generated_hash))
        resultTime = datetime.now(pytz.utc).isoformat()
        merged_anomaly_id = "http://example.com/anomaly/merged/" + urllib.parse.quote(resultTime) + "/" + generated_hash

        merged_anomaly_dict = {
            "id": merged_anomaly_id,
            "update": False,
            "generatedBy": {
                "id": "https://dyversify.ilabt.imec.be/dynamic-dashboard/ns/dynamic-dashboard/1",
                "algo": "Dashboard",
                "version": 1
            },
            "timestamp": resultTime,
            "anomaly": {
                "type": a.atypes,
                "description": RELABEL_DESCRIPTION,
                "parts": [],
                "subanomalies": subanomalies
            }
        }

        merged_anomaly_dict['anomaly']['description'] = self.check_distinct_anomaly_types(anomaly_types_descriptions)

        topic_name = sensor_gateway.kafka_topic_anomalies
        self.write_to_kafka(dumps(merged_anomaly_dict), 'merged', topic_name)

        merged_anomaly = {
            'id': merged_anomaly_id,
            'type': a.atypes,
            'description': merged_anomaly_dict['anomaly']['description'],
            'sensor': list(sensor),
            'property': list(property),
            'from': [min(fromarr)],
            'to': [max(toarr)],
            'resultTime': resultTime,
            'isChecked': False,
            'canEdit': False,
            'mergedAnomalies': anomalies,
            'jsonld': {}
        }
        return merged_anomaly

    def check_distinct_anomaly_types(self, anomaly_types_descriptions):
        description = ''
        a = UnknownPatternAnomaly()
        if a.atype in anomaly_types_descriptions:
            # print('contains unknown anomaly type')
            if len(anomaly_types_descriptions) == 1:
                for k, v in anomaly_types_descriptions.items():
                    if self.all_same(v):
                        description = v[0]
                    else:
                        description = RELABEL_DESCRIPTION
            else:
                anomaly_types_descriptions.pop(a.atype)
                if len(anomaly_types_descriptions) == 1:
                    for k, v in anomaly_types_descriptions.items():
                        if self.all_same(v):
                            description = v[0]
                        else:
                            description = RELABEL_DESCRIPTION
                else:
                    description = RELABEL_DESCRIPTION
        else:
            # print('!contains unknown anomaly type')
            if len(anomaly_types_descriptions) == 1:
                for k, v in anomaly_types_descriptions.items():
                    if self.all_same(v):
                        description = v[0]
                    else:
                        description = RELABEL_DESCRIPTION
            else:
                description = RELABEL_DESCRIPTION
        return description

    @staticmethod
    def write_to_kafka(msg, key_name, topic_name):
        kafka_hosts = settings.KAFKA_BROKERLIST
        print("topic_name: ", topic_name)
        print("kafka_hosts: ", kafka_hosts)
        producer = KafkaProducer(bootstrap_servers=[kafka_hosts])
        # Kafka communication
        try:
            print("\nConnecting to Kafka (writing)")
            # Asynchronous by default
            future = producer.send(topic_name, msg.encode("utf-8"))
            # Block for 'synchronous' sends
            try:
                result = future.get(timeout=10)
            except KafkaError:
                # Decide what to do if produce request failed...
                print("Writing to Kafka topic failed.")
                pass
            print("Connecting to Kafka (writing) - SUCCESS")
            return True
        except Exception as e:
            print("Kafka connection failed:", e.__class__.__name__, e)
            return False
        finally:
            if producer is not None:
                producer.close()
