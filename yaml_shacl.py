import yaml
import requests
import json
import rdflib

def read_in_spec(type):

    if not isinstance(type,str):
        return("Type must be a string.")

    url = 'https://raw.githubusercontent.com/BioSchemas/specifications/master/'+type+'/specification.html'

    req = requests.get(url)
    print(type)
    document = req.content.decode().split('/n')[-1]

    document = document[:document.rfind('\n')]

    specs = yaml.load(document)

    return(specs)


specs = []
types = ['DataCatalog','Dataset','Event','Sample',\
         'Taxon','TrainingMaterial']

for type in types:

    spec = read_in_spec(type)
    specs.append(spec)

shacl_rules = {
    "@context": {
        "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "sh":   "http://www.w3.org/ns/shacl#",
        "xsd":  "http://www.w3.org/2001/XMLSchema#",
        "schema": "http://schema.org/",
        "bio":"http://bioschemas.org/specifications/"
    },
    "sh:shapeGraph":[]
  }

for i in range(len(specs)):

    spec = specs[i]
    type = types[i]

    specGraph = {
        '@id':type + "Shape",
        "@type":"sh:NodeShape",
        "sh:targetClass":"bio:"+type,
        "sh:property":[]
    }

    if not spec.get('properties'):
        continue

    for property in spec.get('properties'):

        prop_dict = {
            "sh:path":"schema:"+property.get('name')
        }

        severity = property.get('marginality')

        if severity == 'Minimum':
            prop_dict['sh:severity'] = 'sh:Violation'
            prop_dict['sh:minCount'] = 1

        elif severity == 'Recommended':
            prop_dict['sh:severity'] = 'sh:Warning'

        cardinality = property.get('cardinality')

        if cardinality == 'ONE':
            prop_dict['sh:maxCount'] = 1

        expected_types = property.get('expected_type')

        if len(expected_types) > 1:

            prop_dict['sh:or'] = []

            for allowed in expected_types:

                prop_dict['sh:or'].append({'sh:class':'schema:' + allowed})

                if allowed == 'Text':
                    prop_dict['sh:or'].append({"sh:datatype": "xsd:string"})

                elif allowed == 'URL':
                    prop_dict['sh:or'].append({"sh:datatype": "xsd:anyURL"})
        else:
            prop_dict['sh:class'] = "schema:" + expected_types[0]

        specGraph['sh:property'].append(prop_dict)

    shacl_rules['sh:shapeGraph'].append(specGraph)

with open('bioschemas_shacl.json','w') as out:
    json.dump(shacl_rules,out,indent=4, separators=(',', ': '))

g = rdflib.Graph()
g.parse("bioschemas_shacl.json", format="json-ld",publicID = "http://bioschemas.org/specifications/")

g.serialize(destination='shacl.ttl', format='turtle')

import fileinput

with fileinput.FileInput('shacl.ttl', inplace=True) as file:
    for line in file:
        print(line.replace('"', ''), end='')
