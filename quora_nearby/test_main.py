#!/usr/bin/python

import sys
import random
import time
import logging
from operator import itemgetter
import kdtree
import test_kdtree
from main import *

def show_topics(topics):
  """ Display the parsed topics. For debugging. """
  
  logging.info("Topics({}): ".format(len(topics)))
  
  for id, topic in topics.iteritems():
    logging.info("  Topic {0}: ({1[x]:0.2f}, {1[y]:0.2f}), with questions {1[value][questions]}".
          format(id, topic))  
    
def show_queries(queries):
  """ Display the parsed queries. For debugging. """
  
  logging.info("Queries({}): ".format(len(queries)))
  commands = {'q': 'question(s)',
              't': 'topic(s)'}
  count = 1
  for query in queries:
    logging.info("  Query {id}: The {query[count]} {type} nearest to ({query[x]:0.2f}, {query[y]:0.2f})".
          format(id=count, query=query, type=commands[query['type']]))
    count += 1  

def test_verbose():
  """ Processes the queries and displays output for checking accuracy, instead
      of just printing out query results. Very verbose, so running this on 
      more than 25 topics or queries is a mistake. """
  
  logging.info("Reading from sys.stdin...")
  data = read_input(sys.stdin)
  
  show_topics(data['topics'])  
  show_queries(data['queries'])  
  
  # Nature of the dataset
  logging.info("There are {} topics, {} questions, and {} queries.".
        format(len(data['topics']), len(data['questions']), len(data['queries'])))
  logging.info("There are {} topics that have no questions.".
        format(data['num_topics_without_questions']))
  logging.info("There are {} questions that have no topics.".
        format(data['num_questions_without_topics']))    

  # Build the topic tree 
  logging.info("Building tree from {} topic points...".format(len(data['topics'])))  
  t0 = time.clock()
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data['topics'], dimensions)
  t1 = time.clock()
  logging.info("Tree constructed, there are {} total nodes ({} s).".
        format(tree.number_nodes, t1 - t0))  
  #logging.info("Here's what the tree structure looks like: ")
  #tree.root.print_tree()
  
  # Build the pruned topic tree for questions queries, with empty topics excluded 
  logging.info("Building pruned tree from {} topic points...".format(len(data['topics_with_questions'])))
  t0 = time.clock()
  dimensions = ['x', 'y']
  pruned_tree = kdtree.KDTree(data['topics_with_questions'].values(), dimensions)
  t1 = time.clock()
  logging.info("Tree constructed, there are {} total nodes ({} s).".
        format(pruned_tree.number_nodes, t1 - t0))    
  #logging.info("Here's what the tree structure looks like: ")
  #pruned_tree.root.print_tree()    

  stats = {}
  for query in data['queries']:
      
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    logging.info("Query: The {query[count]} {type}'s nearest to ({query[x]:0.2f}, {query[y]:0.2f})".
          format(query=query, type=query['type']))    
    
    # Topic queries are straight up nearest neighbor queries.
    if query['type'] == 't':
      
      nearest = tree.k_nearest(query, num_results, stats)
      nearest['list'].sort(key=itemgetter('distance'))
      
      # Just print out the topics
      for count, result in enumerate(nearest['list']):
        logging.info("  Topic {0} - ({1[point]}), distance {1[distance]:0.2f}".format(count, result))
     
      # And some nice info.
      logging.info("  {} nodes (over {} passes) in the {}-node tree were traversed to get this result.".
            format(stats['nodes'],
                   stats['passes'],
                   tree.number_nodes))
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
       
        nearest = tree.k_nearest_linked_records(query, 
                                                num_results, 
                                                'questions', 
                                                data['max_possible_questions'], 
                                                stats)
        
        nearest['questions'].sort(key=itemgetter('distance'))
        
        for count, result in enumerate(nearest['questions']):
          logging.info("  Question {1[id]}, distance {1[distance]:0.2f}".format(count, result))
        
        logging.info("  {} nodes (over {} passes) in the {}-node tree were traversed to get this result.".
            format(stats['nodes'],
                   stats['passes'],
                   tree.number_nodes))   

def generate_data(config, output_filename="stress_test.in"):
  """ Function to generate random test data based on the parameters
      in config. It dumps this data to a file in the format 
      expected by main.
  """
  
  num_topics = config['num_topics']
  
  num_questions = config['num_questions']
  max_topics_per_question = config['max_topics_per_question']  
  
  num_queries = config['num_queries']
  max_results = config['max_results']
  
  side_length = config['side_length']
  origin = config['origin']
    
  output = open(output_filename, 'w')
  
  # Write the beginning line to specify list lengths
  output.write("{} {} {}\n".format(num_topics, num_questions, num_queries))
  
  # Randomly generate topic locations
  topics = test_kdtree.sample_square(origin, side_length, num_topics)         
  
  # Reformat the sample list to have index as topic id
  all_topics = ["{0} {1[x]} {1[y]}\n".format(index, topic) 
                for index, topic in enumerate(topics)]
  
  # Dump all the topics to the file
  output.writelines(all_topics)
  
  questions = []
  for question in range(num_questions):
    
    # Randomly choose a number of topics <= 10 to assign to the question
    num_assigned_topics = random.choice(range(max_topics_per_question))
    
    # Randomly pick that number of topic_id's.
    assigned_topics = random.sample(range(num_topics), num_assigned_topics)
    topic_list = [str(topic) for topic in assigned_topics]
    questions.append("{} {} {}\n".format(question, 
                                         num_assigned_topics, 
                                         ' '.join(topic_list) ))
    
  # Dump all questions to the file
  output.writelines(questions)
  
  commands = ['q', 't']
  queries = []
  query_points = test_kdtree.sample_square(origin, side_length, num_queries)  
  for point in query_points:
    
    # Randomly query on either questions or topics
    command = random.choice(commands)
    num_results = random.choice(range(1, max_results + 1))
                       
    queries.append("{0} {1} {2[x]} {2[y]}\n".
                   format(command, num_results,point))
  
  # Dump all queries to the file
  output.writelines(queries)
  
  output.close()
  
def generate_max_test_data():
  """ Generate test data for quora's limits and dumps it to a file. """
  
  config = {'num_topics': 100,
            'num_questions': 10,
            'num_queries': 10,
            'max_topics_per_question': 10,
            'max_results': 10,
            'side_length': 1000,
            'origin': {'x': 0,
                       'y': 0}}
   
  output_name = "test_{0[num_topics]}_{0[num_questions]}_{0[num_queries]}.in".format(config)         
  generate_data(config, output_name)
  
def test_bruteforce_verbose():
  """ Processes the queries and displays output for checking accuracy, instead
      of just printing out query results. Very verbose, so running this on 
      more than 25 topics or queries is a mistake. """
  
  logging.info("Reading from sys.stdin...")
  data = read_input(sys.stdin)
  
  show_topics(data['topics'])  
  show_queries(data['queries'])  
  
  # Nature of the dataset
  logging.info("There are {} topics, {} questions, and {} queries.".
        format(len(data['topics']), len(data['questions']), len(data['queries'])))
  logging.info("There are {} topics that have no questions.".
        format(data['num_topics_without_questions']))
  logging.info("There are {} questions that have no topics.".
        format(data['num_questions_without_topics']))    

  for query in data['queries']:
      
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    logging.info("Query: The {query[count]} {type}'s nearest to ({query[x]:0.2f}, {query[y]:0.2f})".
          format(query=query, type=query['type']))    
    
    # Topic queries are straight up nearest neighbor queries.
    if query['type'] == 't':
      
      nearest = data['topics'].values()
      nearest.sort(key=lambda k: kdtree.KDTreeNode.distance(k, query) )
      distances = [kdtree.KDTreeNode.distance(k, query) for k in nearest]
      # Just print out the topics
      for count, result in enumerate(nearest[:num_results]):
        logging.info("  Topic {0} - ({1}), distance {2:0.2f}".format(count, result['value']['id'], distances[count]))
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
       
      # We're sorting the dictionary of topics with 1 or more questions, so
      # we know every topic will yield at least one question.
      nearest = data['topics_with_questions'].values()
      nearest.sort(key=lambda k: kdtree.KDTreeNode.distance(k, query) )
      distances = [kdtree.KDTreeNode.distance(k, query) for k in nearest]
      
      # Now all we have to do is aggregate question id's, ignoring duplicates.
      num_questions = 0
      # Keep a separate dictionary for checking duplicates because it doesn't
      # preserve the sorted order.
      dupes = {}
      questions = []
      for topic in nearest:
        
        # Go through the list of question's associated with each topic,
        # adding to the results only if it hasn't previously appeared.
        for question in topic['value']['questions']:
          
          if question not in dupes:
            dupes[question] = True
            questions.append(str(question))
            
        # Break early if we have enough topics
        if len(questions) >= num_results:
          break;
        
      for count, result in enumerate(questions[:num_results]):
        logging.info("  Question {1}, distance {2:0.2f}".format(count, result, distances[count]))
        
def process_queries_brute_force(data):
 """ Function which finds the ids of the nearest neighbors using brute force.
     Used to check accuracy of kd-tree results.
      
      Prints output to stdout as lists of ids (either question or topics,
      depending on what the query requries).
 """
 stats = {}
 for query in data['queries']:
    
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    # Topic search is just a straightforward nearest neighbors query.
    if query['type'] == 't':
      
      # Just pull the values from the topics dictionary and sort by distance
      # from the query point.
      nearest = data['topics'].values()
      nearest.sort(key=lambda k: kdtree.KDTreeNode.distance(k, query) )
      
      
      
      # Re-format for output and print to stdout
      results = [str(result['value']['id']) for result in nearest]
      print(' '.join(results[:num_results]))
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
      
      # We're sorting the dictionary of topics with 1 or more questions, so
      # we know every topic will yield at least one question.
      nearest = data['topics_with_questions'].values()
      nearest.sort(key=lambda k: kdtree.KDTreeNode.distance(k, query) )
      
      # Now all we have to do is aggregate question id's, ignoring duplicates.
      num_questions = 0
      # Keep a separate dictionary for checking duplicates because it doesn't
      # preserve the sorted order.
      dupes = {}
      questions = []
      for topic in nearest:
        
        # Go through the list of question's associated with each topic,
        # adding to the results only if it hasn't previously appeared.
        for question in topic['value']['questions']:
          
          if question not in dupes:
            dupes[question] = True
            questions.append(str(question))
            
        # Break early if we have enough topics
        if len(questions) >= num_results:
          break;
        
      # Re-format for output and print only the number of questions we wanted.
      print(' '.join(questions[:num_results]))
      
def brute_force():    
  """ Function which reads the input and processes queries using a brute force
      approach. For checking accuracy of results from the space partitioning 
      approach ONLY.
      
      With this function you can dump the output of the space partitioning to
      one file and of brute force to another file and compare them line by line.
  """
   
  logging.info("Reading from sys.stdin...")
  
  data = read_input(sys.stdin)
  
  # Actually process the queries
  logging.info("Starting {} brute-force queries...".format(len(data['queries'])))
  t0 = time.clock()
  process_queries_brute_force(data)    
  t1 = time.clock()
  logging.info("Queries finished ({} s)".format(t1-t0))

  
logging.basicConfig(filename='quora_nearby_tree_test.log',level=logging.INFO)
#generate_max_test_data()
test_verbose()