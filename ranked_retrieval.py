import os
import sys
import datetime
import logging
from collections import OrderedDict
import math

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from indexing import *
from search import *
import pprint

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., INFO, DEBUG, WARNING)
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Ranked Search Module") # Log message format
)

# Create a logger instance
logger = logging.getLogger()


def ranked_retrieval(query_list,index):
    start_time= datetime.datetime.now()
    logger.info("Starting Ranked Retrieval at {}".format(start_time))
    
    #tfidf
    '''
    tf=term freq -> no of times term appeard in doc
    for any doc; tf=index.term.postings_list.doc_id.size of list()
    idf= N/doc freq
    N=no of docs=index.term.postings_list.size()
    doc_freq= index.term.doc_freq
    score=1+log(tf)+log(N/df)
    '''
    res={}
    q_num=1
    for query in query_list:

        query=text_cleaner(query)
        query_terms=text_tokenizer(query)
        
        #remove stop words
        stop_words_path="data/english_stop_list.txt"
        with open(stop_words_path,'r') as file:
            stop_word_set=set(file.read().split())
        query_terms=[word for word in query_terms if word not in stop_word_set]
        
        #stemmer
        
        query_terms=text_stemmer(query_terms)
        #concatenate AND between all query terms and do boolean search
        query_terms_bool=" or ".join(query_terms)


        print(query_terms_bool)
        
        bool_search_res=boolean_search([query_terms_bool],index)
        # print(bool_search_res[query_terms_bool]["documents"])

        #for all docs in bool search result,see pos diff for each term if more than 1; break;
        all_docs=bool_search_res[query_terms_bool]["documents"]
        '''
        tf=term freq -> no of times term appeard in doc
        for term in query; tf=index.term.postings_list.doc_id.size of list()
        idf= N/doc freq
        N=no of docs=index.term.postings_list.size()
        doc_freq= index.term.doc_freq
        score=1+log(tf)+log(N/df)
        '''
        #calculate weight
        for doc in all_docs:
            N=len(index["__all_docs__"])
            w=0
            for term in query_terms:
                wtd=0
                if doc in index[term]["postings_list"]:
                    tf=len(index[term]["postings_list"][doc])
                    df=index[term]["doc_freq"]
                else:
                    tf=0
                    df=0
                if tf==0 or df==0:
                    wtd=0
                else:
                    wtd=(1+math.log10(tf))*(math.log10(N/df))
                # idf= N/df if df!=0 else 0
                # print("tf of {} in {} is {}".format(term,doc,tf))
                # print("N/df of {} in {} is {}".format(term,doc,idf))
                w=w+wtd #doc level weight
            if " ".join(query_terms) not in res:
                res[" ".join(query_terms)]=[]

            res[" ".join(query_terms)].append({
                "term":" ".join(query_terms),
                "doc":doc,
                "qnum":q_num,
                "score":w
                })
        q_num=q_num+1
    logger.info("Ranked Retrieval done. Time: {}".format(datetime.datetime.now()-start_time))
    return res






if __name__ == "__main__":
    # processed_text=preprocessor("data/trec.sample.xml")
    # processed_text=preprocessor("data/trec.5000.xml")
    # index_dict=create_inverted_index(processed_text)
    json_index={}
    with open("data/index.json", 'r') as json_file:
        json_index = json.load(json_file)
    logging.info("JSON index loaded")  

    query_list=[]

    with open("data/test_set/queries.ranked.txt",'r') as file:
        for line in file:
            line=line.replace('\n','').split()
            line=" ".join(line[1:])
            query_list.append(line)
    # print(query_list)
    
    ranked_res=ranked_retrieval(query_list,json_index)
    
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(ranked_res)




    with open("data/test_set/result/results.ranked.txt",'w') as file:
        for query in ranked_res:
            sorted_results = sorted(ranked_res[query], key=lambda x: x['score'], reverse=True)
            for res in sorted_results:
                file.write(f"{res['qnum']},{res['doc']},{res['score']}\n")
    logger.info("Ranked retrieval results written to txt file")