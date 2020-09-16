# Scripts for the Watson Potato use case

This folder contains additional materials for the article **Extracting knowledge networks from plant scientific literature: Potato tuber flesh color as an exemplary trait**.

Here you can find the scripts necessary to transform the outputs of Watson Explorer to the results shown in the manuscript.

All scripts used Python 3.4, but should work on any 3.x version.

The process has 3 steps:

1) Extraction of the triples from the WEx files
2) Attribution of additional "labels" to each node (triple subject/object), and splitting of all triples into triple files for each year
3) Transformation into Cytoscape networks

## Step 1: Extraction of triples

Relevant script: `fetch_triples.py`

Inputs: 
* `outputSourceData.json`: a json structure holding the paths to the XMI and XML files, as well as the name of the original documents (from the corpus) they refer to.
* The root directory where the Watson Explorer outputs reside. 

Output: `triples.csv`

## Step 2: Labeling, splitting

Relevant script: `label_and_split_triples.py`
The labeling is done based on the `entities.csv` file, which is a tab-separated text file. The first column holds the text for the entities (subjects/objects) as they appear in the text. The second column has the label for that entity, and the third column has the entity type.

Input: `entities.csv`, `triples.csv`

Output: files in a `triples\[collection_name].csv`, where `[collection_name]` is the title of the collection in question, different for each file.


## Cytoscape network creation

Relevant script: `toCytoscape.py`  
To run this script, you need to be also running an instance of Cytoscape at the same time. See the manuscript for version information.

Input: the `triples\[collection_name].csv` files produced in the previous step

Output: Cytoscape session files, one for each network snapshot (year).


