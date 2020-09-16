#! /usr/bin/env python35
# -*- coding: utf-8 -*-
import os
import codecs
import unicodedata
import csv
import pprint


if __name__ == '__main__':

    # Build dictionary for remapping
    with open('entities.csv', 'r') as entityFile:
        ereader = csv.DictReader(entityFile, delimiter='\t', quotechar='"')
        labels = list()
        for line in ereader:
            labels.append(line)
        entities = dict()
        
        for r in labels:
            sType = r['subjectType']
            surface = str(r['Label']).strip()
            text = str(r['subjectText']).strip()
            if not sType in entities:
                entities[sType] = {}
            entities[sType][text] = surface
        
        if 'subjectType' in entities:
            del entities['subjectType']
        
        # now keys are: Gene_or_Protein, Metabolite, Trait
        #pprint.pprint(entities)
        

    with open('triples.csv', 'r') as triplesAll:
        reader = csv.DictReader(triplesAll, delimiter=';')
        
        entries = list()
        # keys will be:
        # collection; document; sourceCas; relationId; relationMentionId; subjectText; subjectType; subjectPosition; predicate; objectText; objectType; objectPosition
        errorCounter = 0
        for line in reader:
            try:
                line['subjectLabel'] = entities[str(line['subjectType']).strip()][str(line['subjectText']).strip()]
            except KeyError:
                errorCounter += 1
                print(line['subjectType'] + ': ' + line['subjectText'])
                
            try:
                line['objectLabel'] = entities[str(line['objectType']).strip()][str(line['objectText']).strip()]
            except KeyError:
                errorCounter += 1
                print(line['objectType'] + ': ' + line['objectText'])
                
            entries.append(line)

        print('Errors: ' + str(errorCounter))
        collectionNames = list({row['collection'] for row in entries})
        collections = {cn:[] for cn in collectionNames}
        
        for row in entries:
            collections[row['collection']].append(row)
            
        for c in collections:
            print(c + ': ' + str(len(collections[c])))

        fieldOrder = [
            'collection',
            'document',
            'sourceCas',
            'relationId',
            'relationMentionId',
            'subjectLabel',
            'subjectText',
            'subjectType',
            'subjectPosition',
            'predicate',
            'objectLabel',
            'objectText',
            'objectType',
            'objectPosition'
        ]
        if not os.path.exists('triples'):
            os.makedirs('triples')
            
        for c in collections:
            # dr.fieldnames contains values from first row of `f`.
            with open('triples' + os.sep + c + '.csv', 'w', newline='', encoding='utf-8') as fou:
                w = csv.DictWriter(fou, delimiter='\t', fieldnames=fieldOrder)
                headers = {} 
                for n in w.fieldnames:
                    headers[n] = n
                w.writerow(headers)
                for row in collections[c]:
                    w.writerow(row)
    print('Done.')
             
                
                
                
                