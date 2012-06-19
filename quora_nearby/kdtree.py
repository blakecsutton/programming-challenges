import sampling
import math
import sys
from operator import itemgetter

class KDTreeNode():
  
  # This is the axis which the node splits on, e.g. 'x' or 'y'
  axis = None
  # This is the numerical value/location of the splitting axis.
  value = None
  
  # Left and right subtrees
  left_child = None
  right_child = None
  
  # If this it is a leaf node, then we also have the actual data
  # point stored here.
  point = None
  
  def __init__(self, axis=None, value=None, point=None):
    """ Constructor for a kd-tree node, which can be either an internal node
        with a splitting axis and value or a leaf node with a data point.
        
        You must specify either axis and value (for an internal node),
        or point (for a leaf node).
        
        You have to use named arguments to create a leaf node.
    """
    if axis and value and not point:
      self.axis = axis
      self.value = value
    elif point:
      self.point = point
    else:
      msg = "You must specify either axis and value or point."
      raise ValueError(msg)
        
  def nearest(self, query, stats):
    """ Find the single nearest point to the key. """
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(query)
    distance = self.distance(target.point, query)
          
    stats['nodes'] = 0
    min_so_far = {'point': target,
                  'distance': distance}
    # Then search the kd-tree refining the minimum distance, and 
    # using the normal distance along each axis to choose which branch to expand.
    self.find_nearest(query, min_so_far, stats)

    return min_so_far
  
  def find_nearest(self, query, min_so_far, stats):
    
    stats['nodes'] += 1
    
    # Base case: node is a leaf so just compare it.
    if self.is_leaf():
      distance = self.distance(self.point, query)
      
      # Adjust running minimum  if necessary
      if distance < min_so_far['distance']:
        min_so_far['point'] = self
        min_so_far['distance'] = distance
       
    # If there's only a right child, search that branch 
    elif not self.left_child:
      if (query[self.axis] + min_so_far['distance']) > self.value:
        self.right_child.find_nearest(query, min_so_far, stats)
      #self.right_child.find_nearest(query, min_so_far, stats)
      
    # If there's only a left child, search that branch
    elif not self.right_child:
      
      if (query[self.axis] - min_so_far['distance']) <= self.value:
            self.left_child.find_nearest(query, min_so_far, stats)
      #self.left_child.find_nearest(query, min_so_far, stats)
      
    # If the node has both branches, determine which to prioritize and 
    # seach them.
    else:
        # Determine which branch to prioritize
        if query[self.axis] <= self.value:
            first = 'left'
        else:
            first = 'right'

        if first == 'left':
          if (query[self.axis] - min_so_far['distance']) <= self.value:
            self.left_child.find_nearest(query, min_so_far, stats)
          
          if (query[self.axis] + min_so_far['distance']) > self.value:
            self.right_child.find_nearest(query, min_so_far, stats)
  
        else:
          if (query[self.axis] + min_so_far['distance']) > self.value:
            self.right_child.find_nearest(query, min_so_far, stats)   
            
          if (query[self.axis] - min_so_far['distance']) <= self.value:
            self.left_child.find_nearest(query, min_so_far, stats)

  def k_nearest(self, query, k, stats):
    """ Find the k nearest points to the key. """
    
    if k == 1:
      return nearest(query, stats)
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(query)
    distance = self.distance(target.point, query)
    
    stats['nodes'] = 0
    # Change this to a hash table by id later if lists are too slow.
    mins_so_far = {'min_distance': distance,
                   'max_distance': distance,
                   'list': [{'point': target,
                             'distance': distance}]
                   }
    
    # We know we'll always get the one nearest neighbor.
    #
    # What if we find the nearest neighbor to that result, calculate
    # its distance from the query, and use that as the max_distance for the next pass?
    
    # Try something where we slowly increase search radius until
    # we find k nearest neighbors?
    multiplier = 1
    passes = 0
    stat_list = []
    while len(mins_so_far['list']) < k:
      
      #print("Running k-nearest with max_distance = {}".format(mins_so_far['max_distance']))
      mins_so_far['max_distance'] *=  multiplier
      
      # Then search the kd-tree refining the minimum distance, and 
      # using the normal distance along each axis to choose which branch to expand.
      self.find_k_nearest(query, mins_so_far, k, stats)
      
      multiplier += 2
      passes += 1
      
    #print("We looked at {} nodes in {} passes to average out to {} nodes per pass".
    #      format(stats['nodes'], passes, stats['nodes']/passes))
    stats['passes'] = passes

    return mins_so_far

  def insert_min(self, new_min, mins_so_far, k):
    """ Function which inserts a new nearest neighbor into the list of 
        nearest neighbors, ejecting the maximum value if necessary
        to keep the list size at k.
    """
    
    # Consider updating mins to be a hash table by id?
    
    # First make sure it's not already in the list.
    if new_min not in mins_so_far['list']:   
      
      # Adjust the cached minimum distance. We only have to compare against
      # the newly inserted item because items are evicted largest first.
      if new_min['distance'] < mins_so_far['min_distance']:
         mins_so_far['min_distance'] = new_min['distance']     
    
      # If adding the new item to the list will result in k items or less,
      # just append it.
      if len(mins_so_far['list']) < k:
        
        mins_so_far['list'].append(new_min)
          
        # Since nothing is being evicted from the list, we only have to check against
        # the newly inserted item.
        if new_min['distance'] > mins_so_far['max_distance']:
          mins_so_far['max_distance'] = new_min['distance']

      else:
        
        # Find the item with the maximum distance
        max_index = max(range(len(mins_so_far['list'])), 
                        key=lambda k: mins_so_far['list'][k]['distance'])
        
        # And replace it with the new minimum item
        mins_so_far['list'][max_index] = new_min
        
        # Since we kicked out the maximum element max has to be
        # be recalculated at this point.
        max_point = max(mins_so_far['list'],key=itemgetter('distance'))
        mins_so_far['max_distance'] =  max_point['distance']    
      
      """  
      print("Min_list has been updated to:")
      for count, point in enumerate(mins_so_far['list']):
            print("  {0} - ({1[point]}), distance {1[distance]:0.2f}".format(count, point))
      """

  def find_k_nearest(self, query, mins_so_far, k, stats):
    
    stats['nodes'] += 1
    
    # Set the search radius to the maximum distance in the ongoing k nearest neighbors.
    radius = mins_so_far['max_distance']
    
    # Base case: node is a leaf so just compare it.
    if self.is_leaf():
      distance = self.distance(self.point, query)
      
      # Adjust running minimum and add to k nearest neighbors if necessary
      if distance < mins_so_far['max_distance']:
        
        self.insert_min({'point': self,
                         'distance': distance},
                        mins_so_far, 
                        k)

    # If there's only a right child, search that branch 
    elif not self.left_child:
      
      if (query[self.axis] + radius) > self.value:
        self.right_child.find_k_nearest(query, mins_so_far, k, stats)
      
    # If there's only a left child, search that branch
    elif not self.right_child:
      
      if (query[self.axis] - radius) <= self.value:
            self.left_child.find_k_nearest(query, mins_so_far, k, stats)

      
    # If the node has both branches, determine which to prioritize and 
    # seach them.
    else:
        # Determine which branch to prioritize
        if query[self.axis] <= self.value:
            first = 'left'
        else:
            first = 'right'

        if first == 'left':
          if (query[self.axis] - radius) <= self.value:
            self.left_child.find_k_nearest(query, mins_so_far, k, stats)
          
          if (query[self.axis] + radius) > self.value:
            self.right_child.find_k_nearest(query, mins_so_far, k, stats)
  
        else:
          if (query[self.axis] + radius) > self.value:
            self.right_child.find_k_nearest(query, mins_so_far, k, stats)   
            
          if (query[self.axis] - radius) <= self.value:
            self.left_child.find_k_nearest(query, mins_so_far, k, stats)
 
  def is_leaf(self):
    """ Function to test if current node is a leaf, with no children. """
    test = not self.left_child and not self.right_child 
    return test
  
      
  def search(self, query):
    """ Searches the tree to find either the node with the same key or
        or the node that would be the key's parent if it were inserted. 
        Returns a reference to a KDTreeNode. """
        
    # When we reach a leaf it's either equal to the target or
    # equal to the place the target would go.
    if self.is_leaf():
      return self

    # Otherwise the current node defines a splitting line
    # and it's got to have at least one child
    if query[self.axis] <= self.value:
      
      if self.left_child:
        return self.left_child.search(query)
      else:
        # If no left sub-tree, try the right sub-tree
        return self.right_child.search(query)
      
    else:
      
      if self.right_child:
        return self.right_child.search(query)
      else:
        # If no right sub-tree, try the left sub-tree
        return self.left_child.search(query)
  
  @staticmethod  
  def distance(first_point, second_point):
    """ Calculates the squared distance between two points.
        Since we are only using it for comparison we can save
        the time to calculate the square root.
    """
    
    x_diff = first_point['x'] - second_point['x']
    y_diff = first_point['y'] - second_point['y']
    distance = math.sqrt((x_diff * x_diff) + (y_diff * y_diff))
    
    return distance
  
  def __str__(self):
    """ Returns a string representation of the node. """
    return self.__repr__()
    
  def __repr__(self):
    """ Returns a text representation of the node. """
    
    if self.is_leaf(): 
      return "(leaf): ({0[x]:0.2f}, {0[y]:0.2f}) -> {0[value]}".format(self.point)
    else:
      return "({axis}): {value:0.2f}".format(axis=self.axis, value=self.value)
    
  def print_tree(self):
    """ Print out the tree horizontally in levels with notations 
        to show the structure """        
    self.print_tree_helper(0)
    
  def print_tree_helper(self, level):
    """ Print out the tree horizontally """
    
    # Print out a line for this node, indented based on current level.
    spacer = level*'  '
    print("{}{}{}".format(spacer, level, self))
    
    # Now process the children - if they are there, recurse, if they
    # aren't then print a dash to show they aren't there.
    child_level = level+1
  
    # Recurse on left subtree
    if self.left_child:
        self.left_child.print_tree_helper(child_level)
        
    # If there's a left subtree but no right one
    elif self.right_child:
        # Here we are avoiding printing a dash for no child if neither child
        # is present.
        spacer  = child_level*'  '
        print("{}{}: (-)".format(spacer, child_level) )
              
    # Recurse on right subtree
    if self.right_child is not None:
        self.right_child.print_tree_helper(child_level)  
        
    # If there's a right subtree but no left one  
    elif self.left_child is not None:
        print (child_level)*'  '  + str(child_level) + ': ' + '(-)'

  def draw_tree(self, min, max, output_file):
    """ Right now we're only drawing the partition lines, not the actual points. """
    
    if not self.is_leaf():
      
      # Draw a horizontal or vertical line to represent the partition
      if self.axis == 'x':
        start = {'x': self.value, 'y': min['y']}
        end = {'x': self.value, 'y': max['y']}
        
        # Set boundary for next level of partitions
        left_max = {'x': self.value, 'y': max['y']}
        right_min = {'x': self.value, 'y': min['y']}
        
      else:
        start = {'x': min['x'], 'y': self.value,}
        end = {'x': max['x'], 'y': self.value, }
        
        # Set min and max for the left and right subtrees.
        left_max = {'x': max['x'], 'y': self.value}
        right_min = {'x': min['x'], 'y': self.value}
        
      # A two-point series makes a line
      output_file.write("{0[x]} {0[y]}\n".format(start))
      output_file.write("{0[x]} {0[y]}\n".format(end))
      output_file.write("\n")
      
      # Now recurse on any children
      if self.left_child:
        self.left_child.draw_tree(min, left_max, output_file)
      
      if self.right_child:
        self.right_child.draw_tree(right_min, max, output_file)        
      
class KDTree:
  
  root = None
  
  dimensions = None
  number_nodes = 0
  
  def __init__(self, data, dimensions):
    """ Initializes the kd-tree structure using input data, which is expected to
        be any list. 

        Builds the tree by making a list sorted on each dimension,
         choosing the median as current splitting plane, and then creating sublists
         based around it. Leads to a balanced tree but uses more space.
    """
    self.dimensions = dimensions
    self.build_by_sublists(data)
 
  def build_by_sublists(self, data):
      
    # Sort the indexes of the data list, indexing into data[dimension] as the key
    sorted_by = []
    sorted_by.append(sorted(range(len(data)), key=lambda k: data[k]['x']))
    sorted_by.append(sorted(range(len(data)), key=lambda k: data[k]['y']))
    
    self.root = self.split_and_add(data, sorted_by)
    
  def split_and_add(self, data, sublists):
    """ Inputs: 
          data - the list of points in dimensional space
          sublists - a k-length list (k = #dimensions) of the data points
                     sorted by dimension k, as indexes into data.
                     All are equal length.
          dimension - the dimension which the node added by this invocation
                      will split on. Alternates for each level of the tree.
    """ 
    
    # Sanity check
    if len(sublists[0]) != len(sublists[1]):
      print("The sublists are different sizes, something is wrong!")
      
    # Base case: none or 1 item in the sublists.
    size = len(sublists[0])
    if size == 0:
      return None;
    elif size == 1:
      # If there's 1 item in the sublists then create a leaf node and return it.
      self.number_nodes += 1
      return KDTreeNode(point=data[sublists[0][0]])
    
    # Find which dimension has the widest spread
    spreads = []
    for axis, sublist in enumerate(sublists):
      
      # Find the maximum and minimum data value present in the sublist
      max_index = max(sublist, key=lambda k: data[k][self.dimensions[axis]]) 
      max_value = data[max_index][self.dimensions[axis]]
      
      min_index = min(sublist, key=lambda k: data[k][self.dimensions[axis]]) 
      min_value = data[min_index][self.dimensions[axis]]
      
      # Use the max and min coordinates on the current axis to calculate the 
      # spread amount for each sublist
      spread = max_value - min_value
      spreads.append(spread)

    # Pull out the index of the dimension with the max spread,
    # which is the dimensions we will be splitting on for this node.
    dimension = max(range(len(spreads)), key=lambda k: spreads[k])
    
    # We are indexing into the sublist sorted by this dimension so we know
    # where the median is and can then index into the original data list with it.
    median_index = sublists[dimension][size/2] 
    before_median_index = sublists[dimension][(size/2)-1]
    
    # Decide the splitting value for the axis by averaging the two middle elements
    splitting_value = (data[median_index][self.dimensions[dimension]] +
                       data[before_median_index][self.dimensions[dimension]]) / 2                      
    
    # Now create the internal node that defines this splitting line.
    self.number_nodes += 1
    node = KDTreeNode(axis=self.dimensions[dimension],
                      value=splitting_value)
    
    # Create 2 sets of k sublists so we can recurse on each branch. 
    left_sublists = range(len(self.dimensions))
    right_sublists = range(len(self.dimensions))
    
    # For the list sorted by the current dimension, just split it in half.
    left_sublists[dimension] = sublists[dimension][:size/2]
    right_sublists[dimension] = sublists[dimension][size/2:]
     
    # Now do a linear traversal of the other dimensions' lists
    # to partition them based on the splitting axis of the newly created node.
    for axis, value in enumerate(self.dimensions):
      
      # Parittion all lists but the current dimension
      if axis != dimension:
            
        left_sublists[axis] = []
        right_sublists[axis] = []
        for index in sublists[axis]:
          
          # Index into the points list to compare 
          if data[index][self.dimensions[dimension]] <= splitting_value:
             # If the 'x' coordinate of the y-sorted list is less than the x splitting coordinate
             # it should go in the left subtree.
             left_sublists[axis].append(index)
             
          # We ignore values equal to the splitting value because those are already in the tree.
          elif data[index][self.dimensions[dimension]] > splitting_value:
              
              right_sublists[axis].append(index)
                 
    # Recurse on the left and right subtrees using the newly created sublists.)
    node.left_child = self.split_and_add(data, left_sublists)
    node.right_child = self.split_and_add(data, right_sublists)
    
    # Return the reference to the created node/subtree
    return node  
    
  
  def check_balance(self, key):
    """ Function to check how balanced the tree is. 
        Should return something like the greatest differences in # nodes on one side vs.
        another?? """
    pass

  