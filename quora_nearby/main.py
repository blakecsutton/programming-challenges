#!/usr/bin/python

"""
    main.py: a response to Quora's nearby programming challenge.
    
    This is a collection of functions for the Quora nearby programming challenge
    at http://www.quora.com/about/challenges. The object is to process queries to
    find the k nearest topics (or questions, where questions are associated with 0 or 
    more topics) to a two-dimensional point.
    
    To use, pipe in an input file when running this file from the command line.
    If you pass the -log switch, progress will be logged to quora_nearby.log.
    The results of queries are printed to stdout as lists of id's, one query
    per line.
    
    To generate the query results, I parse the input and build two kd-trees
    of topic points, one with all the topic points and one which only has
    topic points with at least one associated question.
    
    To find the k nearest neighbors, I used the nearest neighbor algorithm
    while saving up to k previous estimates for the nearest neighbors.
    Then branches are pruned by checking their partition against the current
    search radius (a function of the distance of the farthest nearest neighbor). 
    With this approach all neighbors returned are guaranteed to be  the nearest, 
    but not all k nearest neighbors may appear in a given 
    radius, so it makes multiple passes (doubling the search radius each time)
    until the k nearest neighbors are found.

"""

import sys
import time
import logging
import kdtree
                                                                                 
def read_input(source):
    """ Function which parses the given source according to the quora nearby
      challenge.
      
            [#topics T] [#questions Q] [#queries N]
            [topic id] [x coordinate] [y coordinate]
            ...    
            [question id] [#topics Qn >= 0] [topic id] ...
            ...
            [command char: q or t] [max # results required] [x] [y]
            ...            
    """      
    
    # Pull out the numbers from the top of the file to set lengths.
    first_line = source.readline().strip()
    first_line = first_line.split(' ')
    num_topics = int(first_line[0])
    num_questions = int(first_line[1])
    
    # Use dictionaries for topics and questions because we want 
    # a fast way to determine links between them.
    topics = {}
    questions = {}
    queries = []
    num_questions_without_topics = 0
    
    # Loop through all the lines in the file, processing them as either
    # a topic, question, or query
    count = 0
    for line in source:
        
        # Trim whitespace and split into separate pieces
        line = line.strip().split(' ')

        if count < num_topics:
            
            topic_id = int(line[0])
            
            # Make a dictionary keyed on the topic_id where each entry points
            # to a list of questions that are in the topic
            topic = {'x': float(line[1]),
                     'y': float(line[2]),
                     'value': {'id': topic_id,
                               'questions': []}}
            topics[topic_id] = topic
            
        elif (count >= num_topics and count < (num_topics + num_questions)): 
            
            question_id = int(line[0])
            questions[question_id] = []
            linked_topics = int(line[1])
            
            if linked_topics > 0:
              # Make a dictionary keyed by question_id where each entry
              # points to a list of topic_id's associated with the question.
              for topic in line[2:]:
                
                topic_id = int(topic)
                questions[question_id].append(topic_id)
                # And put the id of the question in the list field of its topics.
                topics[topic_id]['value']['questions'].append(question_id)

            else:
               # This question has no associated topics, so it can never appear in
               # any search results.
               num_questions_without_topics += 1

        else:
            # Just put the query into a dictionary
            query = {'type': line[0],
                     'count': int(line[1]),
                     'x': float(line[2]),
                     'y': float(line[3]) }
            # And add it to the overall list of queries.
            queries.append(query)    
            
        # And bump the counter that tracks the lines read so far
        count += 1  
    
    # Calculate the number of topics that have no questions attached,
    # and set aside the topics that have at least one question for use 
    # in our question queries. 
    num_topics_without_questions = 0
    topics_with_questions = {}
    for topic_id, topic in topics.iteritems():
      
      if len(topic['value']['questions']) > 0 :
        topics_with_questions[topic_id] = topic
      else:
        num_topics_without_questions += 1
        
    # Calculate the highest number of question results that can be
    # returned for this point set, for sanity checks
    max_possible_questions = len(questions) - num_questions_without_topics
    
    return {'topics': topics,
            'topics_with_questions': topics_with_questions,
            'num_topics_without_questions': num_topics_without_questions,
            'num_questions_without_topics': num_questions_without_topics,
            'max_possible_questions': max_possible_questions,
            'questions': questions, 
            'queries': queries}
                   
def process_queries(data, tree, pruned_tree, stat_list, pass_list):
 """ Function which does the actual work of processing queries by
      searching in the two kd-trees. 
      
      Prints output to stdout as lists of ids (either question or topics,
      depending on what the query requries).
 """
 
 stats = {}
 for query in data['queries']:
    
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    if query['type'] == 't':
      
      # Topic queries are straight up nearest neighbor queries.
      nearest = tree.k_nearest(query, num_results, stats)
      
      # Re-format for output and print
      results = [str(result['point'].point['value']['id']) 
                 for result in nearest['list']]
      print(' '.join(results))
      
      stat_list.append(stats['nodes'])
      pass_list.append(stats['passes'])
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
       
        nearest = pruned_tree.k_nearest_linked_records(query, 
                                                num_results, 
                                                'questions', 
                                                data['max_possible_questions'], 
                                                stats)
  
        # Due to clustering of multiple questions per topic, we could
        # have more question results than we wanted.
        num_records = min(len(nearest['questions']), num_results)
        results = []
        for result in nearest['questions'][:num_records]:
          results.append(str(result['id']) )
        print(' '.join(results))
        
        stat_list.append(stats['nodes'])
        pass_list.append(stats['passes'])      
      
def space_partitioning():
  """ This is the main function for reading the input file, processing queries,
      and printing the results. It takes a space-partitioning approach with
      two kd-trees.  
  """
   
  logging.info("Reading from sys.stdin...")
  
  data = read_input(sys.stdin)
  
  logging.info("Building a tree from {} topic points.".format(len(data['topics'])))
    
  # Build the topics tree
  t0 = time.clock()
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data['topics'], dimensions)
  t1 = time.clock()
  
  logging.info("Tree constructed, there are {} total nodes ({} s).".
          format(tree.number_nodes, t1 - t0))
    
  # Build another tree for questions queries, with empty topics excluded 
  logging.info("Building a tree from {} topic points.".format(len(data['topics_with_questions'])))
  t0 = time.clock()
  dimensions = ['x', 'y']
  pruned_tree = kdtree.KDTree(data['topics_with_questions'].values(), dimensions)
  t1 = time.clock()
  logging.info("Tree constructed, there are {} total nodes ({} s).".
          format(tree.number_nodes, t1 - t0))  
  
  # Actually process the queries
  logging.info("Starting {} queries...".format(len(data['queries'])))
  stat_list = []
  pass_list = []
  t0 = time.clock()
  process_queries(data, tree, pruned_tree, stat_list, pass_list)              
  t1 = time.clock()
  logging.info("Queries finished ({} s)".format(t1-t0))

  # Pull together some analysis for debugging and optimization.
  pass_list.sort()
  logging.info("In {} queries, the number passes was:".
        format(len(data['queries'])))
  logging.info("  {} -> min".format(pass_list[0]))
  logging.info("  {} -> average".format(sum(pass_list)/len(pass_list)))
  logging.info("  {} -> median".format(pass_list[len(pass_list)/2]))
  logging.info("  {} -> max".format(pass_list[-1]))  
  
  stat_list.sort()
  logging.info("In {} queries, the number nodes visited was:".
        format(len(data['queries'])))
  logging.info("  {} -> min".format(stat_list[0]))
  logging.info("  {} -> average".format(sum(stat_list)/len(stat_list)))
  logging.info("  {} -> median".format(stat_list[len(stat_list)/2]))
  logging.info("  {} -> max".format(stat_list[-1]))          

if __name__ == "__main__":
  
  # Turn on logging with -log switch
  if len(sys.argv) > 1:
    if sys.argv[1] == "-log":
      logging.basicConfig(filename='quora_nearby.log',level=logging.INFO)
  
  # Invoke space partitioning 
  space_partitioning()

