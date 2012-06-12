import sampling
import math

class KDTreeNode():
  
  axis = None
  
  key = None
  value = None
  
  parent = None
  left_child = None
  right_child = None
  
  def __init__(self, axis, key, value):
    
    if axis and key and value:
      self.axis = axis
      self.key = key
      self.value = value
      
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
        
  
  def search(self, key):
    
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
  
  def __str__(self):
    """ Returns a string representation of the root node. """
    return self.__repr__()
    
  def __repr__(self):
    """ Returns a text representation of the root node. """
    return " (%0.2f, %0.2f, %s) " % (self.key['x'], self.key['y'], self.value)
    
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


class KDTree:
  
  root = None
  
  def __init__(self, data):
    """ To build the kd-tree, consecutively pull the median from the input list,
        swapping which dimension is used each time. """
        
        
    # Use mod to cycle between x and y dimensions for each level
    dimensions = ['x', 'y']
    count = 0
    dummy_value = "Hulk {}".format(count)
    
    sample_size = 10
    
    # Pull out first median to be the root of the KDTree
    first = sampling.pop_median(data, sample_size, 'x')
    self.root = KDTreeNode(dimensions[count % 2], first, dummy_value)
    
    # Now keep adding the medians to the tree
    for count in range(1, len(data)-1):
      
      dummy_value = "Hulk {}".format(count)
      sample_size = min(len(data), sample_size)
      
      # Pop the median value from the list, rotating which dimension is used each time.
      current = sampling.pop_median(data, sample_size, dimensions[count % 2])
      
      # And insert it into the tree
      self.root.insert(current, dummy_value)
      
  def distance(self, first_key, second_key):
    # Calculate the distance between two points with the Pythagorean Theorem
    
    x_squared = (first_key['x'] - second_key['x']) * (first_key['x'] - second_key['x'])
    y_squared = (first_key['y'] - second_key['y']) * (first_key['y'] - second_key['y'])
    distance = math.sqrt(x_squared + y_squared)
    
    return distance
      
  def nearest(self, key):
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(key)
    min_distance = self.distance(target.key, key)
    
    # Then search the kd-tree refining the minimum distance, and 
    # using the normal distance along each axis to choose which branch to expand.
    
    
    

  def search(self, key):
    return self.root.search(key)
  
  def print_tree(self):
    self.root.print_tree()  
  
 
def check_sampling():
  """ Function to output data for visual checking with xgraph """
  
  origin = {'x': 2, 'y': 1}
  size = 10
  
  data = sampling.sample_square(origin, size, 10)
  copy = data[:]
  
  sampling.display_samples(data)
  
  print("")
  sample_median_index = sampling.get_median(data, 10, 'x')
  
  #print("")
  # Added fake point to make xgraph display the median point correctly
  #print("0 0")
  #display_samples([data[sample_median_index]])

  tree = KDTree(data)
  tree.print_tree()
  
  """
  index = 7
  print("searching for {}".format(copy[index]))
  result = tree.search(copy[index])
  print("Result of searching for ({},{}) is: {}".format(copy[index]['x'], 
                                                        copy[index]['y'], 
                                                        result))
  """
  # Get a test point in the target region for testing nearest neighbor search
  test_point = sampling.sample_square(origin, size, 1)
  print(test_point)
  result = tree.search(test_point[0])
  print("Result of searching for {:0.2f},{:0.2f},) is: {}".format(test_point[0]['x'],
                                                                               test_point[0]['y'],
                                                                               result))

check_sampling()
  
  
  
  
  
  
  
  
  
  
  