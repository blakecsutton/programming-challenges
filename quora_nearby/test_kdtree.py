#!/usr/bin/python

""" test_kdtree.py: test functions for kdtree.py, a kd-tree data structure.
"""

from operator import itemgetter
from collections import Counter
import time
import random
import sys
import kdtree

def sample_square(bottom_left, side_length, quantity):
  """ Returns a list of points (each as a dictionary with 'x' and 'y' keys)
      randomly sampled from the square defined by bottom_left and side_length. 
      quantity indicates the number of points desired (and the size of the returned list). """
  
  points = []
  
  for point in range(quantity):
    
    # Randomly sample a square at the origin
    x = random.uniform(0, side_length)
    y = random.uniform(0, side_length)
    
    # Translate square to bottom_left 
    x += bottom_left['x']
    y += bottom_left['y']
    
    value = "Hulk {}".format(point)
    
    # Add the sample to the list
    points.append({'x': x,
                   'y': y,
                   'value': value})
    
  return points

def partitions_to_file(tree, target, 
                       min_point, max_point, 
                       output_filename="kdtree_parts.out"):
  """ Dump lines representing the splitting axes to a file for plotting.
      min_point and max_point are the lowest and highest points
      possible in the input dataset, respectively, e.g. [0, 0] and [100, 100]  
  
      To visualize all the output in gnuplot, use:
      
      plot "kdtree_parts.out with lines, 
           "samples.out" with points, 
           "search.out" with points
  """
  
  # Dump points used to a text file for plotting
  output_file = open(output_filename, 'w') 
  
  # Write the set of 3-point series representing kd-tree partition lines
  tree.root.draw_tree(min_point, max_point, output_file)
  
  # Dump the search point to the graph as well
  output_file.write("{0[x]} {0[y]}\n".format(target))
  output_file.write("{0[x]} {0[y]}\n".format(target))
  output_file.close()
  
def datapoints_to_file(data, 
                       output_filename="samples.out"):
  """ Dump the datapoints to a file for plotting. """
  
  output_file = open(output_filename, 'w')
  
  for point in data:
    output_file.write("{0[x]} {0[y]}\n".format(point))
    
  output_file.close()
  
def searchpoints_to_file(targets, output_filename="search.out"):
  """ Dump the query points to a file for plotting. """
  
  output_file = open(output_filename, 'w')
  
  for point in targets:
    output_file.write("{0[x]} {0[y]}\n".format(point))
    
  output_file.close()  
  
def stress_test():
  """ This is a function to give an idea of the order of magnitude of running time
      on large inputs. """
      
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 0, 'y': 0}
  size = 1000000
  number = 10000
  data = sample_square(origin, size, number)

  print("Building a 2d-tree from {number} points sampled on a square of size {size}...".
        format(size=size, number=number))
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data, dimensions)

  print("Tree constructed, there are {} total nodes.".format(tree.number_nodes))
  
  stats = {'nodes': 0}
  queries = 10000
  
  print("Randomly generating {} test points for querying the tree...".format(queries))
  test_points = sample_square(origin, size, queries)
  
  print("Test points created.")
  
  print("Start nearest-neighbor queries...")
  t0 = time.clock()
  stat_list = []
  for death in test_points:
    
    # Find the single nearest neighbor to the query point
    result = tree.root.nearest(death, stats)
    stat_list.append(stats['nodes'])
  t1 = time.clock()
  time_elapsed = t1 - t0
  
  # Print some stats to give an idea of the number of nodes traversed.
  print("Queries finished ({} s).".format(time_elapsed))
  
  stat_list.sort()
  print("In {} NN queries, the number nodes visited was:".format(queries))
  print("  {} -> min".format(stat_list[0]))
  print("  {} -> average".format(sum(stat_list)/len(stat_list)))
  print("  {} -> median".format(stat_list[len(stat_list)/2]))
  print("  {} -> max".format(stat_list[-1]))  
  
  k = 10
  print("Starting {}-nearest-neighbor queries...".format(k))
  t0 = time.clock()
  stat_list = []
  pass_list = []
  for death in test_points:
    
    # Find the single nearest neighbor to the query point
    result = tree.root.k_nearest(death, k, stats)
    stat_list.append(stats['nodes'])
    pass_list.append(stats['passes'])

  time_elapsed = time.clock() - t0
  # Print some stats to give an idea of the number of nodes traversed.
  print("Queries finished ({} s)".format(time_elapsed))
  
  pass_list.sort()
  print("In {} {}NN queries, the number passes was:".format(queries, k))
  print("  {} -> min".format(pass_list[0]))
  print("  {} -> average".format(sum(pass_list)/len(pass_list)))
  print("  {} -> median".format(pass_list[len(pass_list)/2]))
  print("  {} -> max".format(pass_list[-1]))  
  
  stat_list.sort()
  print("In {} {}NN queries, the number nodes visited was:".format(queries, k))
  print("  {} -> min".format(stat_list[0]))
  print("  {} -> average".format(sum(stat_list)/len(stat_list)))
  print("  {} -> median".format(stat_list[len(stat_list)/2]))
  print("  {} -> max".format(stat_list[-1]))  

def check_nearest_accuracy():
  """ This is a function for verifying the accuracy of results by
      calculating the actual nearest neighbors by brute force.
      Needless to say this is for debugging only. """
      
  print("Testing the accuracy of nearest neighbor results...")
      
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 0, 'y': 0}
  size = 1000000
  number = 10000
  data = sample_square(origin, size, number)

  print("Building a 2d-tree from {number} points sampled on a square of size {size}...".
        format(size=size, number=number))
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data, dimensions)

  print("Tree constructed, there are {} total nodes.".format(tree.number_nodes))
  
  stats = {'nodes': 0}
  queries = 100
  
  print("Randomly generating {} test points for querying the tree...".format(queries))
  test_points = sample_square(origin, size, queries)
  
  print("Test points created.")
  
  print("Start queries...")
  stat_list = []
  result_list = []
  for test_point in test_points:
    
    # Find the single nearest neighbor to the query point
    nearest = tree.root.nearest(test_point, stats)
    stat_list.append(stats['nodes'])
    
    # Now calculate the actual distances of each point from the target
    # for the purpose of testing accuracy
    all_points = []
    for point in data:
      distance = kdtree.KDTreeNode.distance(point, test_point)
      all_points.append({'x': point['x'],
                         'y': point['y'],
                         'distance': distance})
      
    # Now sort the list of points by distance from the test point and pull out
    # the point with minimum distance
    all_points.sort(key=itemgetter('distance'))
    real_nearest = all_points[0]
       
    # Mark whether the result was correct or not in the result_list. So
    # if result_list[4] is false it means the nearest calculation was wrong for
    # test_points[4]
    # The == operator should work here because the numbers are pulled/calculated
    # in exactly the same way.
    correct = (real_nearest['x'] == nearest['point'].point['x'] and
               real_nearest['y'] == nearest['point'].point['y'] and
               real_nearest['distance'] == nearest['distance'])

    result_list.append(correct)

  # Print some stats to give an idea of the number of nodes traversed.
  print("Queries and testing finished.".format(queries))
  
  frequencies = Counter(result_list)
  print("In {} queries, {} were correct and {} were incorrect.".
        format(queries, frequencies[True], frequencies[False]))

  stat_list.sort()
  print("In {} queries on the {}-node tree, the number nodes visited was:".format(queries,
                                                                                  tree.number_nodes))
  print("  {} -> min".format(stat_list[0]))
  print("  {} -> average".format(sum(stat_list)/len(stat_list)))
  print("  {} -> median".format(stat_list[len(stat_list)/2]))
  print("  {} -> max".format(stat_list[-1]))

def check_k_nearest_accuracy():
  """ This is a function for verifying the accuracy of results by
      calculating the actual nearest neighbors by brute force.
      Needless to say this is for debugging only. """
        
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 0, 'y': 0}
  size = 1000000
  number = 10000
  k = 10
  data = sample_square(origin, size, number)
  
  print("Testing the accuracy of {} nearest neighbors results...")


  print("Building a 2d-tree from {number} points sampled on a square of size {size}...".
        format(size=size, number=number))
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data, dimensions)

  print("Tree constructed, there are {} total nodes.".format(tree.number_nodes))
  
  stats = {'nodes': 0}
  queries = 100
  
  print("Randomly generating {} test points for querying the tree...".format(queries))
  test_points = sample_square(origin, size, queries)
  
  print("Test points created.")
  
  print("Start queries...")
  stat_list = []
  result_list = []
  stats = {}
  for test_point in test_points:
    
    # Find the k nearest neighborsto the query point
    k_nearest = tree.k_nearest(test_point, k, stats)
    
    # Now calculate the actual distances of each point from the target
    # for the purpose of testing accuracy
    all_points = []
    for point in data:
      distance = kdtree.KDTreeNode.distance(point, test_point)
      all_points.append({'x': point['x'],
                         'y': point['y'],
                         'distance': distance})
      
    # Now sort the list of points by distance from the test point and pull out
    # the point with minimum distance
    all_points.sort(key=itemgetter('distance'))
    real_nearest = all_points[:k]

    # Mark whether the result was correct or not in the result_list. So
    # if result_list[4] is false it means the nearest calculation was wrong for
    # test_points[4]
    # The == operator should work here because the numbers are pulled/calculated
    # in exactly the same way.
    for index, neighbor in enumerate(k_nearest['list']):
      correct = (real_nearest[index]['x'] == neighbor['point'].point['x'] and
                 real_nearest[index]['y'] == neighbor['point'].point['y'] and
                 real_nearest[index]['distance'] == neighbor['distance'])
      # Fail out on first non-match.
      if not correct:
        break;

    result_list.append(correct)
    
    if not correct:
      # Print results if they don't match.
      print("Bruteforce results: ")
      
      for index, result in enumerate(real_nearest):
        print("{0}: {1[x]:0.2f}, {1[y]:0.2f}, distance {1[distance]:0.2f}".
              format(index, result))   
      
      print("Kdtree results: ")
     
      for index, neighbor in enumerate(k_nearest['list']):
        print("{0}: {1[x]:0.2f}, {1[y]:0.2f}, distance {2:0.2f}".
              format(index, neighbor['point'].point,  neighbor['distance']))

    

  # Print some stats to give an idea of the number of nodes traversed.
  print("Queries and testing finished.".format(queries))
  
  frequencies = Counter(result_list)
  print("In {} queries, {} were correct and {} were incorrect.".
        format(queries, frequencies[True], frequencies[False]))
  
def check_tree():
  """ This is a function for testing the accuracy of results. """
  
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 2, 'y': 1}
  side_length = 100
  number = 10
  data = sample_square(origin, side_length, number)
  
  print("Building a 2d-tree from {number} points sampled on a square of size {size}...".
        format(size=side_length, number=number))
  
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data, dimensions)

  print("Tree constructed, there are {} total nodes.".format(tree.number_nodes))
  
  # Build a kd-tree, using the sort / scan / sublist method.
  dimensions = ['x', 'y']
  tree = kdtree.KDTree(data, dimensions)
  
  print("Here's what the tree structure looks like: ")
  tree.root.print_tree()
  
  # Test searching for a point that is guaranteed to be in the tree
  print("Searching for a point guaranteed to be in the tree...")
  result = tree.root.search(data[0])
  print("Search result for ({0[x]:0.2f},{0[y]:0.2f}) is: {1}".
        format(data[0], result))         
  
  # Dictionary to hold stats about kd-tree traversals.
  stats = {}
  
  # How many queries to make (and how many random test points to create)
  queries = 1
  print("Randomly generating a test point for querying the tree...".format(queries))
  test_points = sample_square(origin, side_length, queries)                                                                                        
  
  # Test searching for a point not in the tree, to get the potential parent
  print("Searching for a point not in the tree...")
  result = tree.root.search(test_points[0])
  print("Search result for ({0[x]:0.2f},{0[y]:0.2f}) is: {1}".
        format(test_points[0], result))
  
  # Test nearest, which finds the single closest point to the query
  nearest = tree.root.nearest(test_points[0], stats)
  print("Result of nearest for ({p[x]:0.2f},{p[y]:0.2f}) is: {result}".
        format(p=test_points[0], result=nearest['point']))
  
  print("And {} nodes in the {}-node tree were traversed to get this result.".
        format(stats['nodes'],
               tree.number_nodes))
  
  # Test k-nearest, which finds the k nearest points to the query
  num_results = 5
  nearest = tree.root.k_nearest(test_points[0], num_results, stats)
  print("Result of {k}-nearest for ({p[x]:0.2f},{p[y]:0.2f}) is:".
        format(p=test_points[0], k=num_results))

  nearest['list'].sort(key=itemgetter('distance'))
  for count, point in enumerate(nearest['list']):
    print("  {0} - ({1[point]}), distance {1[distance]:0.2f}".format(count, point))
 
    
  print("And {} nodes (over {} passes) in the {}-node tree were traversed to get this result.".
        format(stats['nodes'],
               stats['passes'],
               tree.number_nodes))
    
  # Calculate and display the actual distances of each point from the target
  num_results = 5
  print("And here are the top {} nearest points to the target: ".format(num_results))
  results = []
  for point in data:
    distance = kdtree.KDTreeNode.distance(point, test_points[0])
    results.append({'x': point['x'],
                    'y': point['y'],
                    'distance': distance})
  results.sort(key=itemgetter('distance'))
  for result in results[:num_results]:
    print("  ({0[x]:0.2f}, {0[y]:0.2f}) -> {0[distance]:0.2f}".format(result))

  
  partitions_to_file(tree, 
                     test_points[0], 
                     origin, 
                     {'x': origin['x'] + side_length,
                      'y': origin['y'] + side_length})

  datapoints_to_file(data)
  
  searchpoints_to_file(test_points)

if __name__ == "__main__":  
  
  if len(sys.argv) > 1:
    choice = sys.argv[1]
    if choice == "showtree":
      check_tree()
    elif choice == "accuracy":
      check_nearest_accuracy()
      check_k_nearest_accuracy()
    elif choice == "stresstest":
      print("hmm?")
      stress_test()
    else:
      "Command line argument not recognized."
  else:
    print("Command line argument required: either showtree, accuracy, or stresstest.")
    
  
  
  
  
  
  
  
  
  
