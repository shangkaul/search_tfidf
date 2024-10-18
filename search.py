import os
import sys
import datetime
import logging
from collections import OrderedDict

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from indexing import *
import pprint

# Configure logging to display messages in the console (stdout)
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., INFO, DEBUG, WARNING)
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("Search Module") # Log message format
)

# Create a logger instance
logger = logging.getLogger()

def boolean_search(query_list, index):
    start_time=datetime.datetime.now()
    logging.info("Boolean Search Start time: {}".format(start_time))
    query_results=OrderedDict()
    for query in query_list:
        #pre-process query
        # query_terms=query.lower().split()
        #Cleanup and case folding
        #remove punctuation and replace with ' '
        q=query

        # query=text_cleaner(query)
        #TOkenize but keep phrases intact
        # query_terms=text_tokenizer(query)
        query_terms = re.findall(r'\"[^\"]+\"|\S+', query)
        
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

        # print(query_terms)
        #Create operator and operand stacks
        for term in query_terms:
            term=term.lower()

            if term in operator_precedence.keys():
                #precedence wise operator search
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

                # outside loop -> precedence of current operator is more  -> push to operator stack           
                operator_stack.append(term)
            else:
                # Process phrase operand by using phrase search function
                if term[0]=='"' and term[-1]=='"':
                    phrase = term.strip('"')
                    phrase_result = phrase_search([phrase], index)
                    doc_ids = set(phrase_result)
                else:
                    if term in index:
                        doc_ids=set(index[term]["postings_list"].keys())
                    else:
                        doc_ids=set()
                operand_stack.append(doc_ids)
                # print("doc ids pushed in stack for"+term)
        

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

def phrase_search(query_list,index):
    start_time=datetime.datetime.now()
    logger.info("Phrase search started {}".format(start_time))
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
        
        # query_terms=text_stemmer(query_terms)
        #concatenate AND between all query terms and do boolean search
        query_terms_bool=" and ".join(query_terms)

        # print(query_terms_bool)
        
        bool_search_res=boolean_search([query_terms_bool],index)
        # print(bool_search_res[query_terms_bool]["documents"])

        #for all docs in bool search result,see pos diff for each term if more than 1; break;
        common_docs=bool_search_res[query_terms_bool]["documents"]
        query_terms=text_stemmer(query_terms)
        # print(common_docs)
        doc_list=[]

        for doc in common_docs:
            first_term_pos_list = index[query_terms[0]]["postings_list"][doc]
            

            for pos in first_term_pos_list:
                phrase_match=1
                for i in range(1,len(query_terms)):
                    posting_list_n=index[query_terms[i]]["postings_list"][doc]
                    if pos+1 not in posting_list_n:
                        phrase_match=0
                        break
                if phrase_match>0:
                    doc_list.append(doc)
                    break
    logger.info("Phrase search complete. Time: {}".format(datetime.datetime.now()-start_time))
    return doc_list
    
def proximity_search(query_list,index):
    start_time=datetime.datetime.now()
    logger.info("Proximity search started {}".format(start_time))
    for query in query_list:
        q=query

        query=query.split('(')
        pos_diff=int(query[0].replace('#',''))
        query_terms=query[1].lower().replace(")",'').split(',')

        # query=text_cleaner(query)
        # query_terms=text_tokenizer(query)
        
        #remove stop words
        # stop_words_path="data/english_stop_list.txt"
        # with open(stop_words_path,'r') as file:
            # stop_word_set=set(file.read().split())
        # query_terms=[word for word in query_terms if word not in stop_word_set or word in ["and", "or", "not"]]
        
        #stemmer
        

        #concatenate AND between all query terms and do boolean search
        query_terms_bool=" and ".join(query_terms)

        # print(query_terms_bool)

        
        bool_search_res=boolean_search([query_terms_bool],index)
        # print(bool_search_res[query_terms_bool]["documents"])

        #for all docs in bool search result,see pos diff for each term if more than 1; break;
        common_docs=bool_search_res[query_terms_bool]["documents"]
        query_terms=text_stemmer(query_terms)

        query_terms=[word.strip() for word in query_terms]

        # print(common_docs)
        doc_list=[]

        for doc in common_docs:
            first_term_pos_list=index[query_terms[0]]["postings_list"][doc]

            for pos in first_term_pos_list:
                posting_list_2=index[query_terms[1]]["postings_list"][doc]
                found_match=0
                for next_pos in posting_list_2:
                    # if (pos < next_pos) and (next_pos <= pos + pos_diff): #if order matters -> incom should come bfore tax
                    if abs(pos-next_pos)<=pos_diff:
                        found_match=1
                        break

                if found_match>0:
                    doc_list.append(int(doc))
                    break

        logger.info("Proximity search complete. Time: {}".format(datetime.datetime.now()-start_time))
    return sorted(doc_list)

if __name__ == "__main__":
    # processed_text=preprocessor("data/trec.sample.xml")

    # processed_text=preprocessor("data/trec.5000.xml")
    # index_dict=create_inverted_index(processed_text)
    json_index={}
    with open("data/index.json", 'r') as json_file:
        json_index = json.load(json_file)
    logging.info("JSON index loaded")  

    # print(boolean_search(["Sadness"],json_index))

    # logging.info(type(json_index))  
    
    # Search
    queries=[]
    with open("data/test_set/queries.boolean.txt",'r') as file:
        for line in file:
            queries.append(line.strip())

    res={}
    q_num=1
    for query in queries:
        q=" ".join(query.split()[1:])
        res[q_num]={"q_num":q_num,
                    "query": q,
                    "matches":0,
                    "result":[]}
        
        if '#' in q:
            res[q_num]["result"]=proximity_search([q],json_index)
        else:
            res[q_num]["result"]=boolean_search([q],json_index)[q]["documents"]
        res[q_num]["matches"]=len(res[q_num]["result"])
        q_num+=1


    # pprint.pprint(res)

    with open("data/test_set/result/results.boolean.txt",'w') as file:
        for q in res.keys():
            for doc in res[q]["result"]:
                file.write("{},{}\n".format(q,doc))
                
    logger.info("Result file written")
    

    # bool_search_res=boolean_search(queries[:1],json_index)
    # print(bool_search_res)
    # with open("data/bolean_search.txt",'w') as file:
    #    q_num=1
    #    for query in bool_search_res.keys():
    #        for doc_num in bool_search_res[query]["documents"]:
    #            file.write(str(q_num)+","+str(doc_num)+"\n")
    #        q_num=q_num+1
    # logger.info("Bool search results saved to txt")
    
    # phrase_search_res=boolean_search(['israel and "middle east"'],json_index)
    # print(phrase_search_res)    
    # phrase_search_res=boolean_search(['"middle east" AND israel'],json_index)
    # print(phrase_search_res)

    # phrase_search_res=boolean_search(['"wall street" AND "dow jones"'],json_index)
    # print(phrase_search_res)    
    # phrase_search_res=boolean_search(['"dow jones" and "wall street"'],json_index)
    # print(phrase_search_res)

    # phrase_search_res=boolean_search(['Sadness'],json_index)
    # print(phrase_search_res)   
    
    # phrase_search_res=boolean_search(['glasgow and scotland'],json_index)
    # print(phrase_search_res) 
    # phrase_search_res=boolean_search(['corporate and taxes'],json_index)
    # print(phrase_search_res) 
    # phrase_search_res=boolean_search(['"corporate taxes"'],json_index)
    # print(phrase_search_res) 

    # proximity_search_res=proximity_search(["#30(corporate,taxes)"],json_index)
    # print("matches: {}".format(len(proximity_search_res)))
    # print(proximity_search_res)

    # phrase_search_res=boolean_search(['"middle east" AND israel'],json_index)
    # print(phrase_search_res)    

    # proximity_search_res=proximity_search(["#5(Palestinian, organisations)"],json_index)
    # print("matches: {}".format(len(proximity_search_res)))
    # print(proximity_search_res)

    # phrase_search_res=boolean_search(['"wall street" AND "dow jones"'],json_index)
    # print(phrase_search_res)  
    

    
        

    