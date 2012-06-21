#!/usr/bin/python

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
  # point stored here, which should be a dictionary with keys
  # 'x', 'y', and 'value', which is where any non-location data should go.
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
    """ Find the single nearest point to the key.
    
        We can do this in sublinear time by first finding an upper bound
        for the distance (by finding the query's place in the tree) and
        then only visiting partitions which overlap a square as big as the 
        minimum distance so far.
    
    """
  
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
    """ Recursively find the single nearest point to the query point
        by refining an intial estimate of the nearest neighbor. 
        Prune branches by checking if the partition overlaps the area
        defined by the current minimum distance (min_so_far['distance')
        around the query point. """
    
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
    
    # Short-circuit
    if k == 1:
      result = self.nearest(query, stats)
      return {'list': [result]}
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(query)
    distance = self.distance(target.point, query)
    
    # Change this to a hash table by id later if lists are too slow.
    mins_so_far = {'min_distance': distance,
                   'max_distance': distance,
                   'list': [{'point': target,
                             'distance': distance}]
                   }
    
    # We slowly increase search radius until
    # we find k nearest neighbors
    multiplier = 1
    passes = 0
    stat_list = []
    while len(mins_so_far['list']) < k:
      
      stats['nodes'] = 0
      
      # Catch the case where a query point is exactly on a point in the 
      # tree and no other candidates were found.
      mins_so_far['max_distance'] = max(1, mins_so_far['max_distance'])
      
      mins_so_far['max_distance'] *=  multiplier
      
      # Then search the kd-tree refining the minimum distance, and 
      # using the normal distance along each axis to choose which branch to expand.
      self.find_k_nearest(query, mins_so_far, k, stats)
      mins_so_far['list'].sort(key=itemgetter('distance'))
      
      multiplier += .1
      passes += 1
      
    stats['passes'] = passes

    return mins_so_far
  
  def k_nearest_linked_records(self, query, k, key_name, stats):
    
    # Instead of the number of nodes found, what we care about is
    # the number of unique linked records found
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(query)
    distance = self.distance(target.point, query)
    
    # Change this to a hash table by id later if lists are too slow.
    mins_so_far = {'min_distance': distance,
                   'max_distance': distance,
                   'list': [{'point': target,
                             'distance': distance}]
                   }
    
    # Set up a dictionary to track unique linked record results.
    record_table = {}
    linked_records = []
    
    # We slowly increase search radius until
    # we find k nearest linked records
    multiplier = 1
    stats['nodes'] = 0
    stats['passes'] = 0
    stat_list = []
    num_results = k
    while len(linked_records) < num_results:
      
      # Make passes over the tree, widening the search radius until we
      # get the number of neighbors we wanted
      while len(mins_so_far['list']) < k:
        
        # Catch the case where a query point is exactly on a point in the 
        # tree and no other candidates were found.
        mins_so_far['max_distance'] = max(1, mins_so_far['max_distance'])
        mins_so_far['max_distance'] *=  multiplier
        
        # Then search the kd-tree refining the minimum distance, and 
        # using the normal distance along each axis to choose which branch to expand.
        self.find_k_nearest(query, mins_so_far, k, stats)
        stats['passes'] += 1
        
        multiplier += .1
      
      # Now go through the list of nearest neighbors and process the linked records.
      num_linked = len(linked_records)
      mins_so_far['list'].sort(key=itemgetter('distance'))
      for result in mins_so_far['list']:
      
        # Get the lists of linked records (might be length zero)
        records = result['point'].point['value'][key_name]
          
        # Put question id's in dictionary to eliminate duplicate id's
        for record_id in records:
          if record_id not in record_table:
            record_table[record_id] = result['distance']
            linked_records.append(record_id)
          
      # If we didn't find any new questions, increase k
      if num_linked <= len(linked_records):
        k *= 2
        #print("  Bumping up k to {}".format(k))
    
    # Reformat dictionary into a list for sorting.
    record_list = []
    for record_id in linked_records:
      record_list.append({'id': record_id,
                          'distance': record_table[record_id]})    
      
    mins_so_far[key_name] = record_list
    return mins_so_far
  
  def insert_min(self, new_min, mins_so_far, k):
    """ Function which inserts a new nearest neighbor into the list of 
        nearest neighbors, ejecting the maximum value if necessary
        to keep the list size at k.
    """    
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
      
  def find_k_nearest(self, query, mins_so_far, k, stats):
    """ This is a function to find the k nearest neighbors to the
        query point. It does this by keeping track of old minima
        encountered during the nearest neighbor search in a list
        (mins_so_far), which boots out the maximum value when it 
        gets to be of size higher than k.
        
        This function only visits partitions which intersect with
        the highest distance in the current set of minima, so
        it is fast but not guaranteed to find k minima.
        
        However, all of the points it finds are guaranteed to be 
        the nearest ones to the query.
    """
    
    stats['nodes'] += 1
    
    # Set the search radius to the maximum distance in the ongoing k nearest neighbors.
    radius = mins_so_far['max_distance']
    
    # Base case: node is a leaf so just compare it.
    if self.is_leaf():
      distance = self.distance(self.point, query)
      
      # Adjust running minimum and add to k nearest neighbors if necessary
      if (distance < mins_so_far['max_distance'] or
         len(mins_so_far['list']) < k):
        
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
    """ Calculates the distance between two points.
    """
    
    x_diff = first_point['x'] - second_point['x']
    y_diff = first_point['y'] - second_point['y']
    distance = math.sqrt((x_diff * x_diff) + (y_diff * y_diff))
    
    # If distance is < epsilon, just return 0
    epsilon = .001
    distance = max(0, distance - epsilon)

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
    """ This functions prints a series of lines representing the partitions
        in the tree, so the tree structure can be seen graphically in a plotting
        program. 
        
        min and max are the minimum and maximum points in a bounding box for the
        tree, and output_file is the stream to write the lines to.
    """
    
    # Leaves aren't partitions
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
  leaf_nodes = 0
  
  def __init__(self, data, dimensions):
    """ Initializes the kd-tree structure using input data, which is expected to
        be any list. 
        
        data is a list of dictionaries, and dimensions is a list of the keys used
        to index dimensions in the data, in order, e.g., ['x', 'y']

        We build the tree by making a list sorted on each dimension,
        choosing the median as current splitting plane, and then creating sublists
        based around it. This uses O(n) space and O(nlog n) time.
    """
    self.dimensions = dimensions
    self.build_by_sublists(data)
 
  def build_by_sublists(self, data):
    """ Function that starts the split/partition process. """
      
    # Sort the indexes of the data list, indexing into data[dimension] as the key
    sorted_by = []
    sorted_by.append(sorted(range(len(data)), key=lambda k: data[k]['x']))
    sorted_by.append(sorted(range(len(data)), key=lambda k: data[k]['y']))
    
    self.root = self.split_and_add(data, sorted_by)
    
  def get_splitting_dimension(self, data, sublists):
    """ Given d lists of n items (sublists),
        this function returns the dimension which has the highest spread.
        The dimension is returned as an index into the sublists list. """
    
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
    # which is the dimension we want to partition on.
    dimension = max(range(len(spreads)), key=lambda k: spreads[k])
    
    return dimension    
    
  def split_and_add(self, data, sublists):
    """ Inputs: 
          data - the list of points in dimensional space
          sublists - a k-length list (k = #dimensions) of the data points
                     sorted by dimension k, as indexes into data.
                     All are equal length.
          dimension - the dimension which the node added by this invocation
                      will split on. Alternates for each level of the tree.
    """ 
        
    # Base case: none or 1 item in the sublists.
    size = len(sublists[0])
    if size == 0:
      return None;
    elif size == 1:
      # If there's 1 item in the sublists then create a leaf node and return it.
      self.number_nodes += 1
      self.leaf_nodes += 1
      return KDTreeNode(point=data[sublists[0][0]])
    
    # Choose the dimension with the largest spread to split on
    dimension = self.get_splitting_dimension(data, sublists)
    
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
      
      # Partition all lists but the current dimension
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
  
  def k_nearest(self, query, k, stats):
    """ This is a function to return the k nearest points to the query.
        query must be a dictionary which contains a point location.
        stats should be an empty initialized dictionary, it will be passed
        back with diagnostic information.
        
        k is clipped to the number of data points in the tree.
    """
    # Make sure k is no higher than the total number of points in the tree
    max_possible_results = min(k, self.leaf_nodes)
    
    return self.root.k_nearest(query, max_possible_results, stats)
  
  def k_nearest_linked_records(self, query, k, 
                               key_name, max_possible_records,
                               stats):
    """ This is a function to return the k nearest unique records to the query,
        assuming that each point in the tree has a list of linked records 
        accessible via the key_name in its value dictonary.
        
        max_possible_records is neccessary so that k can be clipped. 
    """
    # Make sure k is no higher than the number of unique linked records in the tree.
    max_possible_results = min(k, max_possible_records)
    return self.root.k_nearest_linked_records(query, max_possible_results, 
                                             key_name, stats)
  