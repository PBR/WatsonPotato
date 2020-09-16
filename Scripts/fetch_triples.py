#! /usr/bin/env python35
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
import codecs
import unicodedata
import os
import csv
import json

ns = {
    'xmi': 'http://www.omg.org/XMI',
    'annotation_type': 'http:///com/ibm/takmi/nlp/annotation_type.ecore',
    'cas': 'http:///uima/cas.ecore',
    'ext': 'http:///com/ibm/es/ext.ecore',
    'neardup': 'http:///com/ibm/es/oze/uima/annotator/neardup.ecore',
    'nlp': 'http:///com/ibm/es/nlp.ecore',
    'nlp2': 'http:///com/ibm/es/oze/nlp.ecore',
    'noNamespace': 'http:///uima/noNamespace.ecore',
    'oze': 'http:///com/ibm/es/oze.ecore',
    'pas': 'http:///com/ibm/es/nlp/pas.ecore',
    'sentiment': 'http:///com/ibm/es/nlp/sentiment.ecore',
    'sire': 'http:///com/ibm/es/ext/sire.ecore',
    'sire2': 'http:///com/ibm/nlp/sire.ecore',
    'social': 'http:///com/ibm/es/oze/social.ecore',
    'systemT': 'http:///com/ibm/systemT.ecore',
    'tcas': 'http:///uima/tcas.ecore',
    'tt': 'http:///com/ibm/es/tt.ecore',
    'tt2': 'http:///uima/tt.ecore',
    'uimatypes': 'http:///com/ibm/langware/uimatypes.ecore'
}


# def remove_special(node):
#     # remove html tags that mess with element tree (like <i> and <sub>)
#     raw = node.text + ''.join(ElementTree.tostring(e, encoding='unicode', method='text') for e in node)
#     # normalise characters (accented and modified letters made simple)
#     ascii = unicodedata.normalize('NFKD', raw).encode('ASCII', 'ignore').decode('ASCII')
#     return ascii
    
    
def makeTriple(relDict):
    t = {'subjectText': relDict['subject']['entityText'],
         'subjectType': relDict['subject']['entityType'],
         'subjectPosition': relDict['subject']['begin'] + '-' + relDict['subject']['end'],
         'predicate': relDict['predicate'],
         'objectText': relDict['object']['entityText'],
         'objectType': relDict['object']['entityType'],
         'objectPosition': relDict['object']['begin'] + '-' + relDict['object']['end'],
         }
    return t
    
    
def getThingById(thingList, thingId):
    for item in thingList:
        if item.get('{http://www.omg.org/XMI}id') == thingId:
            return item
    return 0
    
    
def fetchEntityMentionDetails(sofa, entityMentions2, emId):
    em = getThingById(entityMentions2, emId)
    begin = int(em.get('begin'))
    end = int(em.get('end'))
    entityText = sofa[int(em.get('sofa'))][begin:end]
    entity = {'entityType': em.get('entityType'), 'entityText': entityText, 'begin': str(begin), 'end': str(end)}
    return entity
    
    
def analyzeRM2(sofa, relationMentions2, entityMentions2, rm2id):
    rM = getThingById(relationMentions2, rm2id)
    sofaNum = int(rM.get('sofa'))
    
    # get entities for relation arguments
    subjectEntity = fetchEntityMentionDetails(sofa, entityMentions2, rM.get('arg1'))
    objectEntity = fetchEntityMentionDetails(sofa, entityMentions2, rM.get('arg2'))
    
    begin = int(rM.get('begin'))
    end = int(rM.get('end'))
    #print('\tFull relation sentence: ' + sofa[sofaNum][begin:end])
    
    return subjectEntity, objectEntity
    
    
def analyzeDocument(filename):
    documentRelations = list()
    with codecs.open(filename, encoding='utf-8', mode='r') as f:
        tree = ElementTree.parse(f)
        root = tree.getroot()
        
        # relations1 and relationMentions1 do not link to the actual entities (=type cannot be retrieved), but they supply the text
        # relations1 = root.findall('sire:Relation', ns)
        # relationMentions1 = root.findall('sire:RelationMention', ns)
        metafields = root.findall('oze:MetaField', ns)
        for m in metafields:
            fieldName = m.get('name')
            if fieldName == 'directory':
                colFolderPath = m.get('value')
                colName = colFolderPath.split('/')[-1]
            elif fieldName == 'filename':
                docName = m.get('value')
                
        relations2 = root.findall('sire2:Relation', ns)
        relationMentions2 = root.findall('sire2:RelationMention', ns)
        entityMentions2 = root.findall('sire2:EntityMention', ns)
        
        casView = root.findall('cas:View', ns)
        sofaElem = root.findall('cas:Sofa', ns)
        
        sofaMembers = dict()
        sofa = dict()
        
        for c in casView:
            mem = [int(x) for x in c.get('members').split(' ')]
            sofaMembers[c.get('sofa')] = mem
        
        for s in sofaElem:
            id = int(s.get('{http://www.omg.org/XMI}id'))
            cont = s.get('sofaString')
            sofa[id] = cont
        
        print('Relations (' + str(len(relations2)) + '):')
        for r in relations2:
            relType = r.get('relationType')
            mentionIdList = r.get('mentions').split(' ')
            
            for mentionId in mentionIdList:
                sub, obj = analyzeRM2(sofa, relationMentions2, entityMentions2, mentionId)
                outputRel = {'subject': sub, 'predicate': relType, 'object': obj}
                t = makeTriple(outputRel)
                t['relationMentionId'] = mentionId
                t['sourceCas'] = filename
                t['document'] = docName
                t['collection'] = colName
                t['relationId'] = r.get('{http://www.omg.org/XMI}id')
                documentRelations.append(t)
            
    return documentRelations
    
    
if __name__ == '__main__':
    allRelations = list()
    with open('outputSourceData.json', 'r') as fp:
        outputSourceData = json.load(fp)
    
    relNumberPerCollection = dict()
    #for col in ['C01', 'C02']:  #  for testing
    for col in outputSourceData:
        colRels = list()
        for casFile in outputSourceData[col]['cas']:
            print('Processing: ' + casFile)
            rels = analyzeDocument(casFile)
            allRelations.extend(rels)
            colRels.extend(rels)
        relNumberPerCollection[col] = len(colRels)
        
    for cin in relNumberPerCollection:
        print(cin + ': ' + str(relNumberPerCollection[cin]))
    
    exit()
    fieldOrder = [
        'collection',
        'document',
        'sourceCas',
        'relationId',
        'relationMentionId',
        'subjectText',
        'subjectType',
        'subjectPosition',
        'predicate',
        'objectText',
        'objectType',
        'objectPosition'
    ]
    
    # dr.fieldnames contains values from first row of `f`.
    with open('triples.csv', 'w', newline='', encoding='utf-8') as fou:
        w = csv.DictWriter(fou, delimiter=';', fieldnames=fieldOrder)
        headers = {} 
        for n in w.fieldnames:
            headers[n] = n
        w.writerow(headers)
        for row in allRelations:
            w.writerow(row)
            
        
    print('\nDone.')
