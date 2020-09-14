#! /usr/bin/env python35
# -*- coding: utf-8 -*-
import os
import codecs, unicodedata
import csv, json
import pprint
import random
import copy
import requests
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, Comment
import xml.etree.ElementTree as ET
from py2cytoscape.data.cyrest_client import CyRestClient


# Note that this script uses the Cytoscape API, so an instance of Cytoscape must be running.

merge_dicts = [
    {'group': 'tuber flesh', 
     'members': [
        'flesh',
        'flesh trait',
        'orange flesh',
        'tuber color',
        'tuber flesh',
        'tuber flesh colour',
        'white flesh colour'
     ]
    }
]

keys = [
    {'name': 'SUID', 'type': 'long', 'for': 'node', 'id': 'SUID'},
    {'name': 'shared name', 'type': 'string', 'for': 'node', 'id': 'shared name'},
    {'name': 'name', 'type': 'string', 'for': 'node', 'id': 'name'},
    {'name': 'selected', 'type': 'boolean', 'for': 'node', 'id': 'selected'},
    {'name': 'type', 'type': 'string', 'for': 'node', 'id': 'type'},
    {'name': 'SUID', 'type': 'long', 'for': 'edge', 'id': 'SUID'},
    {'name': 'shared name', 'type': 'string', 'for': 'edge', 'id': 'shared name'},
    {'name': 'shared interaction', 'type': 'string', 'for': 'edge', 'id': 'shared interaction'},
    {'name': 'name', 'type': 'string', 'for': 'edge', 'id': 'name'},
    {'name': 'selected', 'type': 'boolean', 'for': 'edge', 'id': 'selected'},
    {'name': 'interaction', 'type': 'string', 'for': 'edge', 'id': 'interaction'},
    {'name': 'collection', 'type': 'string', 'for': 'edge', 'id': 'collection'},
    {'name': 'document', 'type': 'string', 'for': 'edge', 'id': 'document'},
    {'name': 'sourceCas', 'type': 'string', 'for': 'edge', 'id': 'sourceCas'},
    {'name': 'relationId', 'type': 'string', 'for': 'edge', 'id': 'relationId'},
    {'name': 'relationMentionId', 'type': 'string', 'for': 'edge', 'id': 'relationMentionId'},
    {'name': 'subjectText', 'type': 'string', 'for': 'edge', 'id': 'subjectText'},
    {'name': 'subjectPosition', 'type': 'string', 'for': 'edge', 'id': 'subjectPosition'},
    {'name': 'objectText', 'type': 'string', 'for': 'edge', 'id': 'objectText'},
    {'name': 'objectPosition', 'type': 'string', 'for': 'edge', 'id': 'objectPosition'},
    {'name': 'SUID', 'type': 'long', 'for': 'graph', 'id': 'SUID'},
    {'name': 'shared name', 'type': 'string', 'for': 'graph', 'id': 'shared name'},
    {'name': 'name', 'type': 'string', 'for': 'graph', 'id': 'name'},
    {'name': 'selected', 'type': 'boolean', 'for': 'graph', 'id': 'selected'},
    {'name': '__Annotations', 'type': 'string', 'for': 'graph', 'id': '__Annotations'}
]

def addEntityAttr(xmlEntity, attr, val):
    data = SubElement(xmlEntity, 'data')
    data.set('key', attr)
    data.text = val
    return data

    
def filesOfType(path, ext):
    documentNames = [f for f in os.listdir(path) if f.endswith('.' + ext)]
    return documentNames
    
    
def prepareNetworkEntities(col_filename):
    edges = list()
    nodes = list()
    with open(col_filename, 'r') as triplesAll:
        reader = csv.DictReader(triplesAll, delimiter='\t')
        rowNum = len(list(reader))
        triplesAll.seek(0)
        triplesAll.readline()
        
        errorCounter = 0
        checkNodes = set()
        generated_ids = set(random.sample(range(100, 10000), rowNum * 3))
        # keys will be:
        # collection	document	sourceCas	relationId	relationMentionId	subjectLabel	subjectText	subjectType	subjectPosition	predicate	objectLabel	objectText	objectType	objectPosition
        for line in reader:
            tmpLine = copy.deepcopy(line)
            subjLabel = line['subjectLabel']
            subjType = line['subjectType']
            objLabel = line['objectLabel']
            objType = line['objectType']
            if subjLabel + subjType not in checkNodes:
                checkNodes.add(subjLabel + subjType)
                subjId = str(generated_ids.pop())
                nodes.append({'name': subjLabel, 'type': subjType, 'id': subjId})
                tmpLine['sourceNodeId'] = subjId
            else:
                for item in nodes:
                    if item['name'] == subjLabel and item['type'] == subjType:
                        tmpLine['sourceNodeId'] = item['id']
                        break
            if objLabel + objType not in checkNodes:
                checkNodes.add(objLabel + objType)
                objId = str(generated_ids.pop())
                nodes.append({'name': objLabel, 'type': objType, 'id': objId})
                tmpLine['targetNodeId'] = objId
            else:
                for item in nodes:
                    if item['name'] == objLabel and item['type'] == objType:
                        #tmpLine['targetNodeId'] = objId
                        tmpLine['targetNodeId'] = item['id']
                        break
                
            tmpLine['name'] = subjLabel + ' ' + line['predicate'] + ' ' + objLabel
            tmpLine['id'] = str(generated_ids.pop())
            edges.append(tmpLine)
            
        #for e in edges:
        #    print('slabel: ' + e['subjectLabel'])
        #    print('olabel: ' + e['objectLabel'])
        #    pprint.pprint(e)
        #    exit()
            
    return nodes, edges
    
    
def make_graphml_file(col_filename, nodes, edges):
    top = Element('graphml')
    allkeys = Element('keys')
    top.set('xmlns', 'http://graphml.graphdrawing.org/xmlns')
    graph = SubElement(top, 'graph')
    graph.set('edgedefault',  'directed')
    graph.set('id', col_filename)


    
    # field/attribute declarations
    for k in keys[:]:
        key = SubElement(allkeys, 'key')
        key.set('attr.name', k['name'])
        key.set('attr.type', k['type'])
        key.set('for', k['for'])
        key.set('id', k['id'])
    
    
    for n in nodes:
        node = SubElement(graph, 'node')
        node.set('id', n['id'])

        addEntityAttr(node, 'SUID', n['id'])
        addEntityAttr(node, 'shared name', n['name'])
        addEntityAttr(node, 'name', n['name'])
        addEntityAttr(node, 'selected', 'false')
        addEntityAttr(node, 'type', n['type'])
    
    for e in edges:
        edge = SubElement(graph, 'edge')
        edge.set('source', e['sourceNodeId'])
        edge.set('target', e['targetNodeId'])

        addEntityAttr(edge, 'SUID', e['id'])
        addEntityAttr(edge, 'shared name', e['name'])
        addEntityAttr(edge, 'shared interaction', e['predicate'])
        addEntityAttr(edge, 'name', e['name'])
        addEntityAttr(edge, 'selected', 'false')
        addEntityAttr(edge, 'interaction', e['predicate'])
        addEntityAttr(edge, 'collection', col_filename[:-4])
        addEntityAttr(edge, 'document', e['document'])
        addEntityAttr(edge, 'sourceCas', e['sourceCas'])
        addEntityAttr(edge, 'relationId', e['relationId'])
        addEntityAttr(edge, 'relationMentionId', e['relationMentionId'])
        addEntityAttr(edge, 'subjectText', e['subjectText'])
        addEntityAttr(edge, 'subjectPosition', e['subjectPosition'])
        addEntityAttr(edge, 'objectText', e['objectText'])
        addEntityAttr(edge, 'objectPosition', e['objectPosition'])

    
    textparts = minidom.parseString(ET.tostring(top)).toprettyxml(indent='    ').split('\n', 2)
    
    text = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + textparts[1] +
        minidom.parseString(ET.tostring(allkeys)).toprettyxml(indent='    ')[29:-8] + textparts[2])
    #print(text)
    
    with open(col_filename[:-4] + '.graphml', 'w') as collNetwork_out:
        collNetwork_out.write(text)

    print('GRAPHML file has been written.')
    
    
def graphml2cyto(col_filename, style_filename, outpath):
    cy = CyRestClient()
    cy.session.delete()
    net = cy.network.create_from(col_filename[:-4] + '.graphml')

    entireNetworkJson = requests.get('http://localhost:1234/v1/networks.json')
    entireNetwork = json.loads(entireNetworkJson.text)
    nodes = entireNetwork[0]['elements']['nodes']
    numNodes = json.loads(requests.get('http://localhost:1234/v1/networks/' + str(entireNetwork[0]['data']['SUID']) + '/nodes/count').text)['count']
    numEdges = json.loads(requests.get('http://localhost:1234/v1/networks/' + str(entireNetwork[0]['data']['SUID']) + '/edges/count').text)['count']
    
    for d in merge_dicts:
        merge_ids = [n['data']['SUID'] for n in nodes if n['data']['name'] in d['members']]        
        #pprint.pprint(nodes)

        requests.post('http://127.0.0.1:1234/v1/networks/' + 
            str(entireNetwork[0]['data']['SUID']) + '/groups', 
            data=json.dumps({'name': d['group'],  'nodes': merge_ids}), 
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'})
    
    #with open(style_filename, 'r') as fstyle:
    #    content = fstyle.read()[1:-1]
    #    content = json.loads(content)
    #    print(content)
    #    styleResp = requests.post('http://127.0.0.1:1234/v1/styles/',
    #        data=json.dumps(content), 
    #        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'})
    #    styleName = json.loads(styleResp.text)['title']
    #    print('style name is: ' + styleName)
    #    cy.style.apply(style=styleName, network=net)
            
    cy.layout.apply(name='circular', network=net)
    cy.session.save(outpath)
    cy.session.delete()
    return numNodes, numEdges
    
    
if __name__ == '__main__':
    
    home_folder = 'C:/Users/papou001/DDesktop/Watson/All_output_collections' + os.sep + 'triples'
    #home_folder = 'C:/Users/papou001/DDesktop/cur'
    cyto_folder = home_folder + os.sep + 'Cytoscape_sessions'
    networkStatistics = list()
    if not os.path.exists(cyto_folder):
        os.makedirs(cyto_folder)
    allCollections = sorted(filesOfType(home_folder, 'csv'))
    #allCollections = ['C58-Pubmed_collection_Time_series-2016.csv']
    
    for col_filename in allCollections:
        print('Processing collection: ' + col_filename[:-4])
        # Read and prepare node and edge structures
        nodes, edges = prepareNetworkEntities(col_filename)
    
        # Compose GRAPHML file
        make_graphml_file(col_filename, nodes, edges)
        
        # Transform GRAPHML file into a Cytoscape session file
        numNodes, numEdges = graphml2cyto(col_filename, home_folder + os.sep + 'styles.json', cyto_folder + os.sep + col_filename[:-4] + '.cys')
        networkStatistics.append({
            'network_name': col_filename[:-4],
            'number_of_nodes': str(numNodes),
            'number_of_edges': str(numEdges)
        })
     
        
    with open('summary.csv', 'w', newline='\n', encoding='utf-8') as sfout:
        dict_writer = csv.DictWriter(sfout, {'network_name', 'number_of_nodes', 'number_of_edges'}, delimiter=';')
        dict_writer.writeheader()
        dict_writer.writerows(networkStatistics)
        

    print('Done.')
    
