import os
import sys
import datetime
import logging
from collections import OrderedDict

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from indexing import *

# Configure logging to display messages in the console (stdout)
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., INFO, DEBUG, WARNING)
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Indexing Module") # Log message format
)

# Create a logger instance
logger = logging.getLogger()

def boolean_search(query_list, index):
    start_time=datetime.datetime.now()
    logging.info("Search Start time: {}".format(start_time))
    query_results=OrderedDict()
    for query in query_list:
        #pre-process query
        # query_terms=query.lower().split()
        #Cleanup and case folding
        #remove punctuation and replace with ' '
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

        operand_stack=[]
        operator_stack=[]
        operator_precedence = {"or":1,"and":2,"not":3}
        
        #Create operator and operand stacks
        for term in query_terms:
            if term in operator_precedence.keys():
                while len(operator_stack)>0 and operator_precedence[operator_stack[-1]] >= operator_precedence[term]:
                    op=operator_stack.pop()
                    if op=="not":
                        operand_doc_ids= operand_stack.pop()
                        all_doc_ids=set(index["__all_docs__"])
                        operand_stack.append(all_doc_ids - operand_doc_ids)
                    else: #and and or
                        right_doc_ids=operand_stack.pop()
                        left_doc_ids=operand_stack.pop()

                        if op=="and":
                            operand_stack.append(left_doc_ids & right_doc_ids)
                        elif op=="or":
                            operand_stack.append(left_doc_ids | right_doc_ids)
                operator_stack.append(term)
            else:
                if term in index:
                    doc_ids=set(index[term]["postings_list"].keys())
                else:
                    doc_ids=set()
                
                operand_stack.append(doc_ids)
        
        while operator_stack:
            op=operator_stack.pop()

            if op=="not":
                operand_doc_ids= operand_stack.pop()
                all_doc_ids=set(index["__all_docs__"])
                operand_stack.append(all_doc_ids - operand_doc_ids)
            else: #and and or
                right_doc_ids=operand_stack.pop()
                left_doc_ids=operand_stack.pop()

                if op=="and":
                    operand_stack.append(left_doc_ids & right_doc_ids)
                elif op=="or":
                    operand_stack.append(left_doc_ids | right_doc_ids)
        res_docs=list(operand_stack.pop())
        query_results[query] ={"matches":len(res_docs) ,"documents":res_docs}
    logging.info("Time taken: {}".format(datetime.datetime.now()-start_time))
    return query_results    



if __name__ == "__main__":
    # processed_text=preprocessor("data/trec.sample.xml")
    # index_dict=create_inverted_index(processed_text)
    json_index={}
    with open("data/index.json", 'r') as json_file:
        json_index = json.load(json_file)
    logging.info("JSON index loaded")  

    # logging.info(type(json_index))  
    
    ## Search
    queries=[]
    with open("data/queries.txt",'r') as file:
        for line in file:
            queries.append(line.strip())

    search_res=boolean_search(queries,json_index)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(search_res)
    
        

    