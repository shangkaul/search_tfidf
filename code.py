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
    format="{} : %(asctime)s - %(levelname)s : %(message)s".format("IR Search Module") # Log message format
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
    """
    Prints each document in the provided XML list using pretty printing.

    Args:
        xml (list): A list of XML documents to be printed.

    Returns:
        None
    """
    pp = pprint.PrettyPrinter(indent=4)
    for doc in xml:
        pp.plogging.info(doc)


def text_cleaner(text):
    """
    Cleans the input text by performing the following operations:
    1. Removes all characters except alphanumeric characters, spaces, and hyphens.
    2. Converts the text to lowercase.
    3. Replaces newline characters with spaces.
    4. Replaces double spaces with single spaces.
    5. Replaces hyphens with spaces.
    6. Removes any extra spaces.

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    # cleaned_text=re.sub(r"[^a-zA-Z0-9\s-]", '',text).lower().replace("\n",' ').replace("  "," ")
    cleaned_text=re.sub(r"[^a-zA-Z0-9\s-]", '',text).lower().replace("\n",' ').replace("  "," ").replace('-',' ')
    cleaned_text=re.sub(' +', ' ',cleaned_text)
    return cleaned_text

def text_tokenizer(text):
    """
    Tokenizes the input text by splitting it into words.

    Args:
        text (str): The input string to be tokenized.

    Returns:
        list: A list of words obtained by splitting the input text.
    """
    return text.split()

def stopword_remover(text,stop_word_path):
    """
        Removes stopwords from the given text.

        Args:
            text (list of str): The input text represented as a list of words.
            stop_word_path (str): The file path to the stopwords file. The file should contain stopwords separated by whitespace.

        Returns:
            list of str: The text with stopwords removed.
    """
    file=open(stop_word_path,'r')
    stop_word_set=set(file.read().split())
    file.close()
    return [word for word in text if word not in stop_word_set]

def text_stemmer(text,lang='porter'):
    """
        Stems the words in the given text using the specified stemming algorithm.

        Args:
            text (list of str): A list of words to be stemmed.
            lang (str, optional): The stemming algorithm to use. Defaults to 'porter'.

        Returns:
            list of str: A list of stemmed words.
    """
    ps = Stemmer.Stemmer(lang)
    return [ps.stemWord(word) for word in text]

def preprocessor(input_file_path):
    """
    Preprocesses text data from an XML file.
    This function reads an XML file, cleans and tokenizes the text data, removes stop words, 
    and applies stemming to the text.
    Args:
        input_file_path (str): The file path to the input XML file.
    Returns:
        list: A list of dictionaries, where each dictionary represents a document with preprocessed text.
    """
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
    """
    Creates an inverted index from a list of documents.
    The inverted index is a dictionary where each key is a term, and the value is a tuple containing the document frequency 
    and a dictionary of document IDs with their respective positions of the term.
    Args:
        doc_list (list): A list of documents, where each document is a dictionary with 'id', 'headline', and 'text' keys.
    Returns:
        dict: The inverted index.
    Example:
        Input:
            doc_list = [
                {'id': 1, 'headline': ['Lorem', 'ipsum'], 'text': ['dolor', 'sit', 'amet']},
                {'id': 2, 'headline': ['ipsum', 'Lorem'], 'text': ['amet', 'sit', 'dolor']}
            ]
        Output:
                "Lorem": [2, {1: [1], 2: [2]}],
                "ipsum": [2, {1: [2], 2: [1]}],
                "dolor": [2, {1: [3], 2: [6]}],
                "sit": [2, {1: [4], 2: [5]}],
                "amet": [2, {1: [5], 2: [4]}]
            ]
    The function also writes the index to a text file and a JSON file.
    """
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



def boolean_search(query_list, index):
    """
    Perform a boolean search on the given index using the provided list of queries.
    Args:
        query_list (list of str): A list of query strings to be processed.
        index (dict): An inverted index where keys are terms and values are dictionaries containing postings lists.
    Returns:
        dict: A dictionary where each key is a query and the value is another dictionary with:
            - "matches" (int): The number of documents that match the query.
            - "documents" (list of int): A list of document IDs that match the query.
    The function processes each query by:
        1. Cleaning and tokenizing the query.
        2. Removing stop words.
        3. Stemming the query terms.
        4. Using stacks to evaluate the boolean expressions in the query.
        5. Returning the matching document IDs for each query.
    Note:
        - The function logs the start time and the time taken to perform the search.
        - The function supports the boolean operators "and", "or", and "not".
        - Phrases enclosed in double quotes are treated as single terms and processed using a phrase search function.
    """
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
    """
    Perform a phrase search on the given index using the provided list of queries.
    This function processes each query by cleaning the text, tokenizing it, removing stop words,
    and optionally stemming the terms. It then performs a boolean search to find documents that
    contain all the query terms. For each document in the boolean search results, it checks if
    the terms appear in the correct order to form the phrase.
    Args:
    query_list (list of str): A list of query phrases to search for.
    index (dict): An inverted index where keys are terms and values are dictionaries containing
                      postings lists with document IDs and positions.
    Returns:
        list: A list of document IDs that contain the query phrases.
    """
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
    """
    Perform a proximity search on the given index using the provided query list.
    Args:
        query_list (list of str): A list of proximity queries. Each query should be in the format '#N(term1,term2)' 
                                  where N is the maximum allowed distance between term1 and term2.
        index (dict): An inverted index where keys are terms and values are dictionaries containing document IDs and 
                      their respective postings lists.
    Returns:
        list of int: A sorted list of document IDs that satisfy the proximity search criteria.
    Example:
        query_list = ['#3(income,tax)']
        index = {
            'income': {'postings_list': {1: [1, 5], 2: [2, 8]}},
            'tax': {'postings_list': {1: [3, 10], 2: [5, 12]}}
        }
        result = proximity_search(query_list, index)
        # result would be [1, 2] if both documents satisfy the proximity condition
    """
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

def ranked_retrieval(query_list,index):
    """
    Perform ranked retrieval on a list of queries using a given index.
    This function calculates the TF-IDF score for each document in the index
    based on the terms in the query list. It returns a dictionary containing
    the query terms, document IDs, query numbers, and their respective scores.
    Args:
        query_list (list of str): A list of query strings to be processed.
        index (dict): An index containing term information, postings lists, 
                      and document frequencies.
    Returns:
        dict: A dictionary where keys are concatenated query terms and values 
              are lists of dictionaries with keys 'term', 'doc', 'qnum', and 'score'.
    """
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

    processed_text=preprocessor("data/trec.5000.xml")
    index_dict=create_inverted_index(processed_text)
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
                
    logger.info("Result file written for boolean search")
    
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
