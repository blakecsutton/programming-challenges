import sampling
import math
import sys

class KDTreeNode():
  
  axis = None
  
  key = None
  value = None
  
  parent = None
  left_child = None
  right_child = None
  
  def __init__(self, axis, key, value):
    """ Initialization function: just set internal data. "
        If  axis, key, or value are None then it will raise an error. """
    if axis and key and value:
      self.axis = axis
      self.key = key
      self.value = value
    else:
      raise ValueError("You can't create a KDTreeNode without valid axis, key, and value")
      
  def is_leaf(self):
    """ Function to tell if current node is a leaf """
    if self.left_child or self.right_child:
      return False
    else:
      return True
    
  def get_next_axis(self):
    """ Helper function to handle switching axes between levels """
    if self.axis == 'x':
      return 'y'
    elif self.axis == 'y':
      return 'x'
    
  def insert(self, key, value):
    
    """ To add a node to the tree, first search to find where it should go,
        then add it as a child there. """
    
    if key[self.axis] < self.key[self.axis]:
      
      # If there's a left child, recurse on the left branch
      if self.left_child:
        self.left_child.insert(key, value)
      else:
        
        # Otherwise, make a left child node with the data
        self.left_child = KDTreeNode(self.get_next_axis(), key, value)
        self.left_child.parent = self
        
    else:
      
      if self.right_child:
        self.right_child.insert(key, value)
      else:
        # Otherwise, make a right child node
        self.right_child = KDTreeNode(self.get_next_axis(), key, value)
        self.right_child.parent = self
        
  def nearest(self, key):
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(key)
    current_min = self.distance(target.key, key)
    
    # Then search the kd-tree refining the minimum distance, and 
    # using the normal distance along each axis to choose which branch to expand.
    better = self.find_nearest(key, current_min)
    
    # If a better node was found, return it
    if better:
      best = better
    else:
      best = target
      
    return best
  
  
  def find_nearest(self, key, current_min):
    
    # First calculate distance from current node to target point
    min_distance = current_min
    distance = self.distance(self.key, key)
    result = None
    
    # Adjust running minimum distance if necessary
    if distance < current_min:
      result = self
      # Or add self to the list of running nearest neighbors
      min_distance = distance
      
    
    # Calculate the normal distance from current node to the target,
    # using the axis which applies to the current node
    normal_distance = abs(key[self.axis] - self.key[self.axis])
    
    # If the perpendicular distance to the current node's partition is
    # less than the running minimum distance, then we have to check both
    # branches
    if normal_distance < min_distance:
      
      # Check left branch   
      if self.left_child:
        candidate = self.left_child.find_nearest(key, min_distance)
      
        # Adjust minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < min_distance:
            result = candidate
            min_distance = distance      
      
      # Check right branch
      if self.right_child:
        candidate = self.right_child.find_nearest(key, min_distance)
      
        # Adjust minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < min_distance:
            result = candidate
            min_distance = distance

    else:
      # Otherwise we only have to check one branch
      if key[self.axis] < self.key[self.axis]:
        
        if self.left_child:
          return self.left_child.find_nearest(key, min_distance)
          
      else:
        if self.right_child:
          return self.right_child.find_nearest(key, min_distance)
    
    # Return the final result at the end
    return result
      
     
  def search(self, key):
    """ Searches the tree to find either the node with the same key or
        or the node that would be the key's parent if it were inserted. 
        Returns a reference to a KDTreeNode. """
    
    # Check if the node has exactly the same key as the search
    if self.key == key:
      return self
    
    if key[self.axis] < self.key[self.axis]:
      
      if self.left_child:
        return self.left_child.search(key)
      else:
        # If no left sub-tree, return the current node
        return self
      
    else:
      
      if self.right_child:
        return self.right_child.search(key)
      else:
        # If no right sub-tree, return the current node
        return self
      
  def distance(self, first_key, second_key):
    # Calculate the distance between two points with the Pythagorean Theorem
    
    x_squared = (first_key['x'] - second_key['x']) * (first_key['x'] - second_key['x'])
    y_squared = (first_key['y'] - second_key['y']) * (first_key['y'] - second_key['y'])
    distance = math.sqrt(x_squared + y_squared)
    
    return distance
  
  def __str__(self):
    """ Returns a string representation of the root node. """
    return self.__repr__()
    
  def __repr__(self):
    """ Returns a text representation of the root node. """
    return " (%0.2f, %0.2f) -> %s" % (self.key['x'], self.key['y'], self.value)
    
  def print_tree(self):
    """ Print out the tree horizontally in levels with notations 
        to show the structure """        
    self.print_tree_helper(0)
    
  def print_tree_helper(self, level):
    """ Print out the tree horizontally """
    
    # Print this node by adding its key and value to the string              
    formatted_node = "(%0.2f, %0.2f)-> %s" % (self.key['x'], self.key['y'], str(self.value))
    print level*'  ' + str(level) + '(' + self.axis + '): '+ formatted_node
    
    # Now process the children - if they are there, recurse, if they
    # aren't then print a dash to show they aren't there.
    child_level = level+1
  
    if self.left_child is not None:
        self.left_child.print_tree_helper(child_level)
    elif self.right_child is not None:
        # Here we are avoiding printing a dash for no child if neither child
        # is present.
        print (child_level)*'  '  + str(child_level) + ': ' + '(-)'
    
    if self.right_child is not None:
        self.right_child.print_tree_helper(child_level)    
    elif self.left_child is not None:
        print (child_level)*'  '  + str(child_level) + ': ' + '(-)'

  def draw_tree(self, min, max, output_file):
      
    # Draw a horizontal or vertical line to represent the partition
    if self.axis == 'x':
      start = {'x': self.key['x'], 'y': min['y']}
      end = {'x': self.key['x'], 'y': max['y']}
      
      # Set boundary for next level of partitions
      left_max = {'x': self.key['x'], 'y': max['y']}
      right_min = {'x': self.key['x'], 'y': min['y']}
      
    else:
      start = {'x': min['x'], 'y': self.key['y'],}
      end = {'x': max['x'], 'y': self.key['y'], }
      
      # Set min and max for the left and right subtrees.
      left_max = {'x': max['x'], 'y': self.key['y']}
      right_min = {'x': min['x'], 'y': self.key['y']}
      
    # A two-point series makes a line
    output_file.write("{0[x]} {0[y]}\n".format(start))
    output_file.write("{0[x]} {0[y]}\n".format(self.key))
    output_file.write("{0[x]} {0[y]}\n".format(end))
    output_file.write("\n")
    
    # Now recurse on any children
    if self.left_child:
      self.left_child.draw_tree(min, left_max, output_file)
    
    if self.right_child:
      self.right_child.draw_tree(right_min, max, output_file)        
      
class KDTree:
  
  root = None
  sample_size = None
  
  def __init__(self, data, sample_size):
    """ To build the kd-tree, consecutively pull the median from the input list,
        swapping which dimension is used each time. 
        
        Sample_size indicates the size of samples to take for estimating the median. """
        
    self.sample_size = sample_size 
    
    # Use mod to cycle between x and y dimensions for each level
    dimensions = ['x', 'y']
    count = 0
    dummy_value = "Hulk {}".format(count)
    
    # Pull out first median to be the root of the KDTree
    first = sampling.pop_median(data, sample_size, 'x')
    self.root = KDTreeNode(dimensions[count % 2], first, dummy_value)
    
    # Now keep adding the medians to the tree until there's nothing left.
    count = 1
    while len(data) > 0:
      
      dummy_value = "Hulk {}".format(count)
      sample_size = min(len(data), sample_size)
      
      # Pop the median value from the list, rotating which dimension is used each time.
      current = sampling.pop_median(data, sample_size, dimensions[count % 2])
      
      # And insert it into the tree
      self.root.insert(current, dummy_value)
      
      count += 1
      print("Count is: {}".format(count))

  def nearest(self, key):
    return self.root.nearest(key)
  
  def search(self, key):
    return self.root.search(key)
  
  def print_tree(self):
    self.root.print_tree()  

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
  size = 10
  number = 10
  data = sampling.sample_square(origin, size, number)
  data_copy = data[:]
  
  sampling.display_samples(data)
  
  sample_size = 0
  tree = KDTree(data, sample_size)
  tree.print_tree()
  
  index = 7
  result = tree.search(data_copy[index])
  print("Result of searching for ({0[x]},{0[y]}) is: {1}".format(data_copy[index], 
                                                        result))                                              
                                                  
  # Create a test point in the target region for testing nearest neighbor search
  test_point = sampling.sample_square(origin, size, 1)
  result = tree.search(test_point[0])
  print("Result of searching for ({:0.2f},{:0.2f}) is: {}".format(test_point[0]['x'],
                                                                  test_point[0]['y'],
                                                                  result))
  
  nearest = tree.nearest(test_point[0])
  print("Result of nearest for ({0[x]:0.2f},{0[y]:0.2f}) is: {1}".format(test_point[0],
                                                                         nearest))
  output_file = open("parts.out", 'w')
  
  # Dump series representing partition lines to stdout
  tree.root.draw_tree(origin, {'x': 12, 'y': 11}, output_file)
  
  # Dump the search point to the graph as well
  output_file.write("{0[x]} {0[y]}\n".format(test_point[0]))
  output_file.write("{0[x]} {0[y]}\n".format(test_point[0]))
  
  output_file.close()
  
  

#check_sampling()
check_tree()

  
  
  
  
  
  
  
  
  
  