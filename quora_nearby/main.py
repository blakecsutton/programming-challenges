#!/usr/bin/python

import sys
import kdtree
import sampling
import random
from operator import itemgetter
import time

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

def generate_stress_data(output_filename="stress_test.in"):

  num_topics = 10000
  num_questions = 1000
  num_queries = 10000
  
  max_topics_per_question = 10
  max_results = 10
  
  # Randomly generate 
  side_length = 1000000
  origin = {'x': 0,
            'y': 0}
  topics = sampling.sample_square(origin, side_length, num_topics)         
  
  output = open(output_filename, 'w')
  
  # Write the beginning line to specify list lengths
  output.write("{} {} {}\n".format(num_topics, num_questions, num_queries))
  
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
  query_points = sampling.sample_square(origin, side_length, num_queries)  
  for point in query_points:
    
    command = random.choice(commands)
    num_results = random.choice(range(1, max_results + 1))
                       
    queries.append("{0} {1} {2[x]} {2[y]}\n".format(command, 
                                                    num_results,
                                                    point))
  
  # Dump all queries to the file
  output.writelines(queries)
  
  
  output.close()
                                                                                 
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
    orphans = 0
    
    # List of queries to be processed
    queries = []
    
    count = 0
    for line in source:
        
        # Trim whitespace and split into separate pieces
        line = line.strip().split(' ')

        if count < num_topics:
            # Process topic line
            topic_id = int(line[0])
            
            # Make a dictionary keyed on the topic_id where each entry points
            # to a list of questions that are in the topic
            topic = {'x': float(line[1]),
                     'y': float(line[2]),
                     'value': {'id': topic_id,
                               'questions': []}}
            topics[topic_id] = topic
            
        elif (count >= num_topics and count < (num_topics + num_questions)): 
            # Process question line
            question_id = int(line[0])
            questions[question_id] = []
            
            linked_topics = int(line[1])
            if linked_topics > 0:
              # Make a dictionary keyed by question_id where each entry
              # points to a list of topic id's associated with the question.
              for topic in line[2:]:
                
                topic_id = int(topic)
                questions[question_id].append(topic_id)
                # And put the id of the question in the list field of its topics.
                topics[topic_id]['value']['questions'].append(question_id)
            else:
               # This question has no associated topics, so it can never appear in
               # any search results.
               orphans += 1
               
               # Also track orphan topics, which can never appear in any question queries??
        else:
            num_results = int(line[1])
                          
            # Put the query into a dictionary
            query = {'type': line[0],
                     'count': num_results,
                     'x': float(line[2]),
                     'y': float(line[3]) }
            # And add it to the overall list of queries.
            queries.append(query)    
            
        count += 1
        
    # Calculate the highest number of question results that can be
    # returned for this point set, for error checking
    max_questions = len(questions) - orphans
    
    return {'topics': topics,
            'max_questions': max_questions,
            'questions': questions, 
            'queries': queries}
    
def show_topics():
  print("Topics({}): ".format(len(data['topics'])))
  
  for id, topic in data['topics'].iteritems():
    print("  Topic {0}: ({1[x]:0.2f}, {1[y]:0.2f}), with questions {1[value][questions]}".
          format(id, topic))  
    
def show_queries():
  print("Queries({}): ".format(len(data['queries'])))
  commands = {'q': 'question(s)',
              't': 'topic(s)'}
  count = 1
  for query in data['queries']:
    print("  Query {id}: The {query[count]} {type} nearest to ({query[x]:0.2f}, {query[y]:0.2f})".
          format(id=count, query=query, type=commands[query['type']]))
    count += 1  
        
def test_main():
  
  print("Reading from sys.stdin...")
  data = read_input(sys.stdin)

  show_topics(data['topics'])  
  show_queries(data['queries'])

  # Build the tree 
  print("Building a tree from {} topic points.".format(len(data['topics'])))
  t0 = time.clock()
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data['topics'], dimensions)
  t1 = time.clock()
  print("Tree constructed, there are {} total nodes ({} s).".format(tree.number_nodes,
                                                                  t1 - t0))
  print("Here's what the tree structure looks like: ")
  tree.root.print_tree()
  
  stats = {}
  for query in data['queries']:
      
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    print("Query {id}: The {query[count]} {type} nearest to ({query[x]:0.2f}, {query[y]:0.2f})".
          format(id=count, query=query, type=commands[query['type']]))    
    
    # Topic queries are straight up nearest neighbor queries.
    if query['type'] == 't':
      
      nearest = tree.k_nearest(query, num_results, stats)
      nearest['list'].sort(key=itemgetter('distance'))
      
      # Just print out the topics
      for count, result in enumerate(nearest['list']):
        print("  Topic {0} - ({1[point]}), distance {1[distance]:0.2f}".format(count, result))
     
      # And some nice info.
      print("  {} nodes (over {} passes) in the {}-node tree were traversed to get this result.".
            format(stats['nodes'],
                   stats['passes'],
                   tree.number_nodes))
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
       
        nearest = tree.k_nearest_linked_records(query, 
                                                num_results, 
                                                'questions', 
                                                data['max_questions'], 
                                                stats)
        
        nearest['questions'].sort(key=itemgetter('distance'))
        
        for count, result in enumerate(nearest['questions']):
          print("  Question {1[id]}, distance {1[distance]:0.2f}".format(count, result))
        
        print("  {} nodes (over {} passes) in the {}-node tree were traversed to get this result.".
            format(stats['nodes'],
                   stats['passes'],
                   tree.number_nodes))    
      
def stress_test():        
   
  print("Reading from sys.stdin...")
  data = read_input(sys.stdin)

  # Build the tree 
  print("Building a tree from {} topic points.".format(len(data['topics'])))
  t0 = time.clock()
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data['topics'], dimensions)
  t1 = time.clock()
  print("Tree constructed, there are {} total nodes ({} s).".
        format(tree.number_nodes, t1 - t0))
  
  print("Questions with at least one topic: {}".format(data['max_questions']))
   
  print("Starting {} queries...".format(len(data['queries'])))
  stats = {}
  stat_list = []
  pass_list = []
  t0 = time.clock()
  for query in data['queries']:
      
    # Pull out the number of results desired for the query.
    num_results = query['count']
    
    if query['type'] == 't':
      
      # Topic queries are straight up nearest neighbor queries.
      nearest = tree.k_nearest(query, num_results, stats)
      nearest['list'].sort(key=itemgetter('distance'))
      
      # Re-format for output and print
      results = [str(result['point'].point['value']['id']) 
                 for result in nearest['list']]
      print(' '.join(results))
      
      stat_list.append(stats['nodes'])
      pass_list.append(stats['passes'])
      
    # Otherwise search is more complicated because we care about number of 
    # records associated with the nearest point(s)
    elif query['type'] == 'q':
       
        nearest = tree.k_nearest_linked_records(query, 
                                                num_results, 
                                                'questions', 
                                                data['max_questions'], 
                                                stats)

        nearest['questions'].sort(key=itemgetter('distance'))
        
        results = []
        for result in nearest['questions']:
          results.append(str(result['id']) )
        print(' '.join(results))
        
        stat_list.append(stats['nodes'])
        pass_list.append(stats['passes'])        
        
  t1 = time.clock()
  print("Queries finished ({} s)".format(t1-t0))

  pass_list.sort()
  print("In {} queries, the number passes was:".
        format(len(data['queries'])))
  print("  {} -> min".format(pass_list[0]))
  print("  {} -> average".format(sum(pass_list)/len(pass_list)))
  print("  {} -> median".format(pass_list[len(pass_list)/2]))
  print("  {} -> max".format(pass_list[-1]))  
  
  stat_list.sort()
  print("In {} queries, the number nodes visited was:".
        format(len(data['queries'])))
  print("  {} -> min".format(stat_list[0]))
  print("  {} -> average".format(sum(stat_list)/len(stat_list)))
  print("  {} -> median".format(stat_list[len(stat_list)/2]))
  print("  {} -> max".format(stat_list[-1]))               

if __name__ == "__main__":
  
  #generate_stress_data("test_10000.in")
  stress_test()

