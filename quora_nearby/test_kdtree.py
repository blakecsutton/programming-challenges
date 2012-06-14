import kdtree
import sampling
from operator import itemgetter

def  check_sampling():
  """ Function to output data for visual checking with xgraph """  
  
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 2, 'y': 1}
  size = 10
  number = 10
  # data becomes a list of point dictionaries
  data = sampling.sample_square(origin, size, number)
  
  # Dump the dataset to a file for graphing
  output_file = open("median.out", 'w')
  for point in data:
    output_file.write("{0[x]:f} {0[y]:f}\n".format(point))
  
  sample_size = 10
  # Dump the estimated median as a point
  sample_median_index = sampling.get_median(data, sample_size, 'x')
  output_file.write("\n")
  output_file.write("{0[x]} {0[y]}\n".format(data[sample_median_index]))
  output_file.write("0 0\n")
  
  sample_median_index = sampling.get_median(data, sample_size, 'y')
  output_file.write("\n")
  output_file.write("{0[x]} {0[y]}\n".format(data[sample_median_index]))
  output_file.write("0 0\n\n")
  
  output_file.close()

def check_tree():
  
  # Sample number points randomly on a square of specified origin and size.
  origin = {'x': 2, 'y': 1}
  size = 100
  number = 50
  data = sampling.sample_square(origin, size, number)
  data_copy = data[:]
  
  #sampling.display_samples(data)

  sample_size = 10
  tree = kdtree.KDTree(data, sample_size)
  tree.print_tree()
  
  """
  # Test searching for a point that is guaranteed to be in the tree
  index = random.choice(range(len(data)))
  result = tree.search(data_copy[index])
  print("Result of searching for ({0[x]:0.2f},{0[y]:0.2f}) is: {1}".format(data_copy[index], result))                                                                                             
  """
  
  # Create a test point in the target region for testing nearest neighbor search
  test_point = sampling.sample_square(origin, size, 1)
  
  # Test search, which finds the node which would be the target point's parent
  result = tree.search(test_point[0])
  print("Result of searching for ({0[x]:0.2f},{0[y]:0.2f}) is: {1}".
        format(test_point[0], result))
  
  # Test nearest, which findest the closest point to the target.
  nearest = tree.nearest(test_point[0])
  print("Result of nearest for ({p[x]:0.2f},{p[y]:0.2f}) is: {result}".
        format(p=test_point[0], result=nearest))
    
  # Test k-nearest, which findest the k closest points to the target.
  #
  # Weird thing I can't figure out: the last result is always off, so
  # you can do a cheaty workaround and ask for 1 more neighbor than you
  # actually want to get accurate results.
  k = 5
  num_results = k+1
  nearest = tree.k_nearest(test_point[0], num_results)
  print("Result of {k}-nearest for ({p[x]:0.2f},{p[y]:0.2f}) is:".
        format(p=test_point[0], k=num_results))
  count = 1
  for point in nearest:
    print("  {0} - ({1[node]}), distance {1[distance]:0.2f}".format(count, point))
    count += 1  
  

  # Calculate and display the actual distances of each point from the target
  print("Actual distances from target: ")
  results = []
  for point in data_copy:
    distance = kdtree.KDTreeNode.distance(point, test_point[0])
    results.append({'x': point['x'],
                    'y': point['y'],
                    'distance': distance})
  results.sort(key=itemgetter('distance'))
  for result in results[:num_results]:
    print("  ({0[x]:0.2f}, {0[y]:0.2f}) -> {0[distance]:0.2f}".format(result))
  
  # Dump points used to a text file for plotting
  output_file = open("parts.out", 'w') 
  # Dump series representing partition lines to stdout
  min = origin
  max = {'x': origin['x'] + size,
         'y': origin['y'] + size}
  tree.root.draw_tree(min, max, output_file)
  
  # Dump the search point to the graph as well
  output_file.write("{0[x]} {0[y]}\n".format(test_point[0]))
  output_file.write("{0[x]} {0[y]}\n".format(test_point[0]))
  output_file.close()
  
  
if __name__ == "__main__":  
  #check_sampling()
  check_tree()

  
  
  
  
  
  
  
  
  
