import sys

""" Quora Programming Challenge 1: Nearby
    
    Input: read from STDIN
    
    Format: [#topics T] [#questions Q] [#queries N]
            [topic id] [x coordinate] [y coordinate]
            ...    
            [question id] [#topics Qn >= 0] [topic id] ...
            ...
            [command char: q or t] [max # results required] [x] [y]
            ...

            distance (break ties by preferring higher ID)
"""

def read_input(source):
    first_line = source.readline().strip()
    first_line = first_line.split(' ')
    
    num_topics = int(first_line[0])
    num_questions = int(first_line[1])
    
    # Probably want to put this into a data structure organized by location
    # kd-tree?
    topics = {}
    
    # Want a reliable way to both look up associated topics given a question 
    # and associated questions given a topic
    questions = {}
    
    # List of queries to be processed
    queries = []
    
    count = 0
    for line in source:
        
        # Trim whitespace and split into separate pieces
        line = line.strip().split(' ')
	print("Read in line {} ".format(count) )      
	print(line) 
        if count < num_topics:
            # Process topic line
            pass
            
        elif (count >= num_topics and count < (num_topics + num_questions)): 
            # Process question line
            pass
        else:
            # Put the query into a dictionary
            query = {'type': line[0],
                     'count': line[1],
                     'x': line[2],
                     'y': line[3] }
            # And add it to the overall list of queries.
            queries.append(query)    
            
        count += 1
    
    return {'queries': queries}
        
    
print("Reading input file...")
data = read_input(sys.stdin)
print("Queries: ")
print(data['queries'])
