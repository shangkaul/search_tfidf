import pprint
import xml.etree.ElementTree as ET
import re
import Stemmer
import datetime
import json
from collections import OrderedDict
import logging
import math

# Configure logging to display messages in the console (stdout)
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., INFO, DEBUG, WARNING)
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Indexing Module") # Log message format
)

# Create a logger instance
logger = logging.getLogger()



def read_xml(file_path):
    '''
    Reads and parses an XML file.
    '''
    tree = ET.parse(file_path)
    root = tree.getroot()
    doc_list=[]
    for doc in root:
        doc_list.append({
            "id":doc.find('DOCNO').text.strip(),
            "headline":doc.find('HEADLINE').text.strip(),
            "text":doc.find('TEXT').text.strip()}
        )
    return doc_list


    
def print_xml(xml):
    pp = pprint.PrettyPrinter(indent=4)
    for doc in xml:
        pp.plogging.info(doc)


def text_cleaner(text):
    # cleaned_text=re.sub(r"[^a-zA-Z0-9\s-]", '',text).lower().replace("\n",' ').replace("  "," ")
    cleaned_text=re.sub(r"[^a-zA-Z0-9\s-]", '',text).lower().replace("\n",' ').replace("  "," ").replace('-',' ')
    cleaned_text=re.sub(' +', ' ',cleaned_text)
    return cleaned_text

def text_tokenizer(text):
    return text.split()

def stopword_remover(text,stop_word_path):
    file=open(stop_word_path,'r')
    stop_word_set=set(file.read().split())
    file.close()
    return [word for word in text if word not in stop_word_set]

def text_stemmer(text,lang='porter'):
    ps = Stemmer.Stemmer(lang)
    return [ps.stemWord(word) for word in text]

def preprocessor(input_file_path):
    logging.info("Starting text pre-processing")
    start_time=datetime.datetime.now()
    logging.info("Start time: {}".format(start_time))

    doc_list=read_xml(input_file_path)

    pp = pprint.PrettyPrinter(indent=4)
    stop_words_path="data/english_stop_list.txt"


    # tokenize, case fold, clean punctuation
    for doc in doc_list:
        #Cleanup and case folding
        #remove punctuation and replace with ' '
        
        doc['headline']=text_cleaner(doc['headline'])
        doc['text']=text_cleaner(doc['text'])
   
        #tokenize()
        doc['headline']=text_tokenizer(doc['headline'])
        doc['text']=text_tokenizer(doc['text'])
        
        #remove stop words
        doc['headline']=stopword_remover(doc['headline'],stop_words_path)
        doc['text']=stopword_remover(doc['text'],stop_words_path)

        #stemmer
        doc['headline']=text_stemmer(doc['headline'])
        doc['text']=text_stemmer(doc['text'])

    logging.info("Preprocessing completed")
    logging.info("Time Taken: {}".format(datetime.datetime.now()-start_time))
    
    return doc_list

def create_inverted_index(doc_list):
    #Creating an index:
    logging.info("Starting Index creation")
    start_time=datetime.datetime.now()
    logging.info("Start time: {}".format(start_time))
    '''
    For all terms in ascensding order, index contains -
    term: document freq
        doc1:pos_list
        doc2: pos_list
        .
        .
        .
    '''
    #format= 
    '''
    {"string=term":(df,{doc 1:[],doc2:[]})}

    example:
    {
        "Lorem":[5,{
                    12:[1,56,33]
                    78:[5]
                    95:[44,55,676]
                    101:[1,2,3,99]
                    157:[90]
                    }],
        "Ipsum":[3,{
                    12:[5,36,34]
                    78:[51,98]
                    95:[43,45,76]
                    }]
    }
    '''
    index={}
    all_docs = set()
    for doc in doc_list:
        doc_id = doc['id']
        all_docs.add(doc_id)
        pos=1
        for word in doc['headline']+doc['text']:
            if word not in index:
                index[word]=[1,{doc['id']:[pos]}]
            else: #word already in index
                #doc id in child dict
                if doc['id'] in index[word][1].keys():
                    index[word][1][doc['id']].append(pos)
                else:#doc id not in child dict
                    index[word][0]+=1
                    index[word][1][doc['id']]=[pos]
            pos=pos+1


    with open("data/test_set/result/index.txt",'w') as file:
        for k in sorted(index.keys()):
            file.write(str(k)+":"+str(index[k][0]))
            file.write("\n")

            for doc in index[k][1].keys():
                file.write("        "+doc+": ")
                # logging.info(",".join(index[k][1][doc]))
                # logging.info(" ")
                file.write(','.join(str(pos) for pos in index[k][1][doc]))
                # file.write(str(posList))
                file.write("\n")
            file.write("\n")
        logging.info("Index file written to txt")
        
        json_index = {"__all_docs__": list(all_docs)}

        for term, (doc_freq, postings) in sorted(index.items()):
            json_index[term] = {
                "doc_freq": doc_freq,
                "postings_list": {
                     str(doc_id): positions for doc_id, positions in postings.items()
                    }
                }
            
        with open("data/index.json", 'w') as json_file:
            json.dump(json_index, json_file, indent=4)
        logging.info("Index file written to json")
        
    logging.info("Time Taken: {}".format(datetime.datetime.now()-start_time))
    logging.info(" ")
    return index






if __name__ == "__main__":

    processed_text=preprocessor("data/trec.5000.xml")
    # processed_text=preprocessor("data/trec.sample.xml")
    index_dict=create_inverted_index(processed_text)
    # pass