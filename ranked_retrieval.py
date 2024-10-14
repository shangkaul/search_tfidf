import os
import sys
import datetime
import logging
from collections import OrderedDict

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from indexing import *
from search import *

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., INFO, DEBUG, WARNING)
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Ranked Search Module") # Log message format
)

# Create a logger instance
logger = logging.getLogger()


def ranked_retrieval(query_list,index):
    
    #tfidf
    '''
    tf=term freq -> no of times term appeard in doc
    for any doc; tf=index.term.postings_list.doc_id.size of list()
    idf= N/doc freq
    N=no of docs=index.term.postings_list.size()
    doc_freq= index.term.doc_freq
    score=1+log(tf)+log(N/df)
    '''
    for query in query_list:
        q=query

        query=text_cleaner(query)
        query_terms=text_tokenizer(query)
        
        #remove stop words
        stop_words_path="data/english_stop_list.txt"
        with open(stop_words_path,'r') as file:
            stop_word_set=set(file.read().split())
        query_terms=[word for word in query_terms if word not in stop_word_set or word in ["and", "or", "not"]]
        
        #stemmer
        
        query_terms=text_stemmer(query_terms)
        #concatenate AND between all query terms and do boolean search
        query_terms_bool=" or ".join(query_terms)

        print(query_terms_bool)
        
        bool_search_res=boolean_search([query_terms_bool],index)
        # print(bool_search_res[query_terms_bool]["documents"])

        #for all docs in bool search result,see pos diff for each term if more than 1; break;
        common_docs=bool_search_res[query_terms_bool]["documents"]
        # print()



if __name__ == "__main__":
    # processed_text=preprocessor("data/trec.sample.xml")
    # index_dict=create_inverted_index(processed_text)
    json_index={}
    with open("data/index.json", 'r') as json_file:
        json_index = json.load(json_file)
    logging.info("JSON index loaded")  

    query_list=[]

    with open("data/ranked_queries.txt",'r') as file:
        for line in file:
            line=line.replace('\n','').split()
            line=" ".join(line[1:])
            query_list.append(line)
    
    ranked_res=ranked_retrieval(query_list,json_index)


    