
import re
from rdflib import Graph, Literal, URIRef

import requests
import gzip
import io


fix_graph = False

wikidata_graph = Graph()
# TASK 1
wikidata_graph.add((
    URIRef("http://www.wikidata.org/entity/Q634"),
    URIRef("http://www.wikidata.org/prop/direct/P3950"),
    URIRef("http://purl.obolibrary.org/obo/ENVO_0100080")
))
wikidata_graph.add((
    URIRef("http://www.wikidata.org/entity/P18"),
    URIRef("http://www.wikidata.org/prop/direct/P2236"),
    URIRef("https://schema.org/screenshot")
))
# TASK 2
wikidata_graph.add((
    URIRef("http://test-subject.org/test"),
    URIRef("http://www.wikidata.org/prop/direct-normalized/TEST"),
    URIRef("http://test-object.org/test")
))
# TASK 3
wikidata_graph.add((
    URIRef("http://www.wikidata.org/entity/Q43449"),
    URIRef("http://www.wikidata.org/prop/direct/P2037"),
    Literal("creativecommons")
))


mapping_graph = Graph()


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
    "http://www.w3.org/2000/01/rdf-schema#subPropertyOf",
    "http://www.wikidata.org/prop/direct/P2236":
    "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
}


# TASK 3
def make_formatter_url_dict():
    string_object_dict = {}

    prefix = "http://www.wikidata.org/entity/"
    # NOTE: P2427 is invalid
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
        if returned_object:
            formatted_url = str(returned_object)
        else:
            # TODO when no formatter url exists; empty so will return string
            formatted_url = ""
        string_object_dict[url_id] = formatted_url

    return string_object_dict


def make_updates(original_triple, new_triple):
    mapping_graph.add(new_triple)
    if fix_graph:
        wikidata_graph.remove(original_triple)
        wikidata_graph.add(new_triple)


def main():
    string_object_dict = make_formatter_url_dict()
    # output mapping graph

    # output_file = "latest-all.ttl.gz"

    # wikidata_graph = Graph()
    # with gzip.open(output_file, "rt", encoding="utf-8") as ttl_stream:
    #     wikidata_graph.parse(ttl_stream, format="turtle")

    for subj, pred, obj in wikidata_graph:

        # wikidata_graph.parse(data=chunk, format="turtle")
        for subj, pred, obj in wikidata_graph:

            original_triple = (subj, pred, obj)

            pred_str = str(pred)

            # TASK 1
            if pred_str in pred_dict:
                new_pred = URIRef(pred_dict[pred_str])
                new_triple = (subj, new_pred, obj)

                # SWAP subj & obj for this predicate
                if pred_str == "http://www.wikidata.org/prop/direct/P2236":
                    new_triple = (obj, new_pred, subj)

                make_updates(original_triple, new_triple)
                continue

            # TASK 2: prefix adjust (direct-normalized)
            old_prefix = "http://www.wikidata.org/prop/direct-normalized/"
            new_pred = URIRef("http://www.w3.org/2004/02/skos/core#exactMatch")

            new_triple = None
            if pred_str.startswith(old_prefix):
                new_triple = (subj, new_pred, obj)

                make_updates(original_triple, new_triple)
                continue

            # TASK 3
            # if the object is a string in rdflib
            new_triple = None
            if isinstance(obj, Literal):

                # if predicate starts with either, get formatter url from dict
                text1 = "http://www.wikidata.org/prop/direct/"
                new_pred = URIRef("http://www.w3.org/2004/02/skos/core#exactMatch")

                if pred_str.startswith((text1)):
                    entity_id = pred_str.removeprefix(text1)
                    formatter_url = string_object_dict[entity_id]
                    new_obj = URIRef(re.sub(r"\$1", obj, formatter_url))
                    new_triple = (subj, new_pred, new_obj)

                    make_updates(original_triple, new_triple)


    # with requests.get(url, stream=True) as response:
    #     response.raise_for_status()
    #     with open(output_file, "wb") as f:
    #         for chunk in response.iter_content(chunk_size=8192):
    #             f.write(chunk)

    # wikidata_graph = Graph()
    # with gzip.open(output_file, "rt", encoding="utf-8") as ttl_stream:
    #     wikidata_graph.parse(ttl_stream, format="turtle")

    # chunk_size = 8192

    # with gzip.open(output_file, "rt", encoding="utf-8") as ttl_stream:
    #     chunk = ""
    #     for line in ttl_stream:
    #         print(line)
    #         try:
    #             for subj, pred, obj in line:
    #                 print(f"{subj} -- {pred} --> {obj}")
    #         except:
    #             pass
    #         chunk += line
    #         if len(chunk) >= chunk_size:
    #             process_chunk(chunk)
    #             chunk = ""

    #     if chunk:
    #         process_chunk(chunk)

    print("\nwiki graph")
    for subj, pred, obj in wikidata_graph:
        print(subj, "--", pred, "--", obj)

    print("\nmapping graph")
    for subj, pred, obj in mapping_graph:
        print(subj, "--", pred, "--", obj)

    mapping_graph.serialize("mapping_graph_complete_NEW.ttl", format="turtle")


if __name__ == "__main__":
    main()
