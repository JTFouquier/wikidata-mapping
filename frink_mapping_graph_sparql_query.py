
import re
from rdflib import Graph, Literal, URIRef
import rdflib.plugins
import rdflib.plugins.sparql
import rdflib
import json

import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://query.wikidata.org/sparql"

fix_graph = False

# wikidata_graph = Graph()
# # TASK 1
# wikidata_graph.add((
#     URIRef("http://www.wikidata.org/entity/Q634"),
#     URIRef("http://www.wikidata.org/prop/direct/P2888"),
#     URIRef("http://purl.obolibrary.org/obo/ENVO_0100080")
# ))
# wikidata_graph.add((
#     URIRef("http://www.wikidata.org/entity/P18"),
#     URIRef("http://www.wikidata.org/prop/direct/P2236"),
#     URIRef("https://schema.org/screenshot")
# ))
# # TASK 2
# wikidata_graph.add((
#     URIRef("http://www.wikidata.org/test"),
#     URIRef("http://www.wikidata.org/prop/direct-normalized/TEST"),
#     URIRef("http://www.wikidata.org/test")
# ))
# # TASK 3
# wikidata_graph.add((
#     URIRef("http://www.wikidata.org/entity/Q43449"),
#     URIRef("http://www.wikidata.org/prop/direct/P2037"),
#     Literal("creativecommons")
# ))
# wikidata_graph.add((
#     URIRef("http://www.lala.org/entity/P18"),
#     URIRef("http://www.lala.org/prop/direct/P2236"),
#     URIRef("https://lala.org/screenshot")
# ))

# TASK 1
pred_dict = {
    "http://www.wikidata.org/prop/direct/P2888":
    "http://www.w3.org/2004/02/skos/core#exactMatch",
    "http://www.wikidata.org/prop/direct/P1709":
    "http://www.w3.org/2002/07/owl#equivalentClass",
    "http://www.wikidata.org/prop/direct/P3950":
    "http://www.w3.org/2004/02/skos/core#narrowMatch",
    "http://www.wikidata.org/prop/direct/P1628":
    "http://www.w3.org/2002/07/owl#equivalentProperty",
    "http://www.wikidata.org/prop/direct/P2235":
    "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
}


def main():
    # log_file = "log.txt"
    # sys.stdout = open(log_file, "w", encoding="utf-8")
    # Complete wiki dump
    # output_file = "latest-all.ttl.gz"
    # wikidata_graph = Graph()
    # with gzip.open(output_file, "rt", encoding="utf-8") as ttl_stream:
    #     wikidata_graph.parse(ttl_stream, format="turtle")

    def get_results(endpoint_url, query):
        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        try:
            return sparql.query().convert()
        except json.JSONDecodeError as e:
            raw_response = sparql.query().response.read().decode("utf-8", errors="ignore")
            clean_response = re.sub(r"[\x00-\x1F\x7F]", "", raw_response)
            try:
                return json.loads(clean_response)
            except json.JSONDecodeError:
                return None

    def use_sparql_query(pred, task):
        # looks messy, but for some reason easier for me to read this way

        # only need subj obj
        if task == "ONEANDTWO":
            query = """SELECT distinct ?subj ?obj WHERE {
            ?subj"""
            query += " <" + pred + "> "
            query += """
            ?obj .
            FILTER (STRSTARTS(STR(?subj), "http://www.wikidata.org/"))
            }
            """

        if task == "THREE":
            query = """SELECT distinct ?subj ?pred ?obj WHERE {
            ?subj ?pred ?obj .
            """
            query += """VALUES ?pred {"""
            query += pred
            query += """
            }
            FILTER (STRSTARTS(STR(?subj), "http://www.wikidata.org/"))
            FILTER isLiteral(?obj)
            }
            """
        # print(query)
        results = get_results(endpoint_url, query)
        return results

    # TASK 3
    def make_formatter_url_dict():
        string_object_dict = {}

        prefix = "http://www.wikidata.org/entity/"
        url_list = ["P2037", "P10283", "P6782", "P882", "P2892", "P3624",
                    "P3151", "P7471"]
        prop_formatter_url = "http://www.wikidata.org/prop/direct/P1630"

        for url_id in url_list:
            url = prefix + url_id
            g = Graph()
            g.parse(url, format="rdf")

            subject = URIRef(url)
            predicate = URIRef(prop_formatter_url)

            returned_object = g.value(subject, predicate)
            formatted_url = str(returned_object)

            string_object_dict[url_id] = formatted_url
        return string_object_dict

    string_object_dict = make_formatter_url_dict()

    mapping_graph = Graph()

    print("TASK 1")
    predicates = ["http://www.wikidata.org/prop/direct/P2888",
                  "http://www.wikidata.org/prop/direct/P1709",
                  "http://www.wikidata.org/prop/direct/P3950",
                  "http://www.wikidata.org/prop/direct/P1628",
                  "http://www.wikidata.org/prop/direct/P2235",
                  "http://www.wikidata.org/prop/direct/P2236"]

    for pred in predicates:
        results = use_sparql_query(pred, "ONEANDTWO")
        for result in results["results"]["bindings"]:
            subj = result['subj']['value']
            obj = result['obj']['value']

            # TASK 1 swap obj & subj
            if str(pred) == "http://www.wikidata.org/prop/direct/P2236":
                mapping_graph.add((URIRef(obj), URIRef("http://www.w3.org/2000/01/rdf-schema#subPropertyOf"), URIRef(subj)))
                continue

            # TASK 1
            if str(pred) in pred_dict.keys():
                mapping_graph.add((URIRef(subj), URIRef(pred_dict[str(pred)]),
                                   URIRef(obj)))
                continue

    print("TASK 2")  # TASK 2: prefix adjust (direct-normalized)
    # Query from Task 2 from Mahir
    query = """select distinct ?property ?propertyLabel (str(?normalizedPredicate_) as ?normalizedPredicate) {
        ?property wikibase:propertyType wikibase:ExternalId ; wdt:P1921 [] ; wikibase:directClaimNormalized ?normalizedPredicate_ .
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
    }
    """
    # get query results (normalizedPredicates)
    results = get_results(endpoint_url, query)
    predicates = [i["normalizedPredicate"]["value"] for i in results["results"]["bindings"]]

    bad_predicates = []
    pred_count = 0
    for pred in predicates:
        print(pred_count)
        pred_count += 1
        results = use_sparql_query(pred, task="ONEANDTWO")
        if results is None:
            bad_predicates.append(pred)
        else:
            for result in results["results"]["bindings"]:
                subj = result['subj']['value']
                obj = result['obj']['value']
                # print(subj, pred, obj)
                mapping_graph.add((URIRef(subj), URIRef("http://www.w3.org/2004/02/skos/core#exactMatch"), URIRef(obj)))

    with open("bad_predicates_task2_list.txt", "w", encoding="utf-8") as f:
        for pred in bad_predicates:
            f.write(f"{pred}\n")

    print("TASK 3")
    # NOTE: P2427 is invalid
    predicates3a = """
    <http://www.wikidata.org/prop/direct/P2037>
    <http://www.wikidata.org/prop/direct/P10283>
    <http://www.wikidata.org/prop/direct/P6782>
    <http://www.wikidata.org/prop/direct/P882>
    <http://www.wikidata.org/prop/direct/P2892>
    """

    predicates3b = """
    <http://www.wikidata.org/prop/direct/P3624>
    <http://www.wikidata.org/prop/direct/P3151>
    <http://www.wikidata.org/prop/direct/P7471>
    """

    # TASK 3 object is a string in rdflib
    for predicates in [predicates3a, predicates3b]:

        results = use_sparql_query(predicates, task="THREE")
        for result in results["results"]["bindings"]:
            subj = result['subj']['value']
            pred = result['pred']['value']
            obj = result['obj']['value']

            # NOTE This space is problematic
            if obj == "NVIDIA Omniverse":
                print("nVIDIA")
                continue
            else:
                pass

            # if pred starts with this, get formatter url from dict
            entity_id = str(pred).removeprefix("http://www.wikidata.org/prop/direct/")
            formatter_url = string_object_dict[entity_id]

            obj = re.sub(r"\$1", obj, formatter_url)

            # fix the url to use the string
            mapping_graph.add((URIRef(subj), URIRef("http://www.w3.org/2004/02/skos/core#exactMatch"), URIRef(obj)))

    print("SERIALIZE")
    with open("mapping_graph_final-20250403.ttl", "wb") as f:
        mapping_graph.serialize(destination=f, format="turtle")


if __name__ == "__main__":
    main()
