import sampling
import math
import sys
from operator import itemgetter

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
    """ Find the single nearest point to the key. """
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(key)
    min_so_far = self.distance(target.key, key)
    
    # Then search the kd-tree refining the minimum distance, and 
    # using the normal distance along each axis to choose which branch to expand.
    better = self.find_nearest(key, min_so_far)
    
    # If a better node was found, return it
    if better:
      best = better
    else:
      best = target

    return best

  def find_nearest(self, key, min_so_far):
    
    # First calculate distance from current node to target point
    current_min = min_so_far
    distance = self.distance(self.key, key)
    result = None
    
    # Adjust running minimum distance if necessary
    if distance < current_min:
      result = self
      current_min = distance
      
    # Calculate the normal distance from current node to the target,
    # using the axis which applies to the current node
    normal_distance = abs(key[self.axis] - self.key[self.axis])
    
    # If the perpendicular distance to the current node's partition is
    # less than the running minimum distance, then we have to check both
    # branches
    if normal_distance < current_min:
      
      # Check left branch   
      if self.left_child:
        candidate = self.left_child.find_nearest(key, current_min)
      
        # Adjust minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < current_min:
            result = candidate
            current_min = distance     
      
      # Check right branch
      if self.right_child:
        candidate = self.right_child.find_nearest(key, current_min)
      
        # Adjust minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < current_min:
            result = candidate
            current_min = distance
  
    else:
      # Otherwise we only have to check one branch
      if key[self.axis] < self.key[self.axis]:
        
        if self.left_child:
          return self.left_child.find_nearest(key, current_min)
          
      else:
        if self.right_child:
          return self.right_child.find_nearest(key, current_min)
    
    # Return the final result at the end
    return result  
  
  def k_nearest(self, key, k):
    
    # Find the node where the key would be inserted and take that as the starting point
    target = self.search(key)
    min_so_far = self.distance(target.key, key)
    
    # Start out list of k-nearest with the first estimate for nearest neighbor.
    k_nearest = [{'node': target,
                  'distance': min_so_far}]
    
    stats = {'nodes': 0}
    # Then search the kd-tree refining the minimum distance, and 
    # using the normal distance along each axis to choose which branch to expand.
    better = self.find_k_nearest(key, min_so_far, k_nearest, k, stats)
    print ("Nodes visited: {0[nodes]}".format(stats))

    # We don't care about the best result returned, we have that information in
    # the list of k nearest neighbors.      
    k_nearest.sort(key=itemgetter('distance'))
    return k_nearest
    
  def find_k_nearest(self, key, min_so_far, k_nearest, k, stats):
    
    stats['nodes'] += 1
    
    # First calculate distance from current node to target point
    current_min = min_so_far
    distance = self.distance(self.key, key)
    result = None
    
    # Adjust running minimum distance if necessary
    if distance < current_min:
      result = self
      current_min = distance
      
      # And add this node to the list of running nearest neighbors
      new_min = {'node': result, 
                 'distance': distance}
      self.insert_min(new_min, k_nearest, k)
        
    # If we don't have k points yet or the distance is < max distnace in k_nearest,
    # add the current node to k_nearest even if it's NOT the minimum
    elif (len(k_nearest) < k or 
          distance < max(k_nearest, key=itemgetter('distance'))):
      
      new_min = {'node': self, 
                 'distance': distance}
      self.insert_min(new_min, k_nearest, k)
    
     
    # Calculate the normal distance from current node to the target,
    # using the axis which applies to the current node
    normal_distance = abs(key[self.axis] - self.key[self.axis])
    
    # If the perpendicular distance to the current node's partition is
    # less than the maximum distance in the k nearest neighbors, we might
    # need to bleed over the partition to replace one of the neighbors.
    if (normal_distance < current_min):
      
      # Check left branch   
      if self.left_child:
        candidate = self.left_child.find_k_nearest(key, current_min, k_nearest, k, stats)
      
        # If we got back a new minimum-distance node, adjust the running minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < current_min:
            result = candidate
            current_min = distance     
            
          # Add this node to the list of running nearest neighbors if it qualifies
          if distance < max(k_nearest, key=itemgetter('distance')):
            new_min = {'node': candidate, # this used to be result?
                       'distance': distance}
            self.insert_min(new_min, k_nearest, k) 
      
      # Check right branch
      if self.right_child:
        candidate = self.right_child.find_k_nearest(key, current_min, k_nearest, k, stats)
      
        # Adjust minimum
        if candidate:
          distance =  self.distance(candidate.key ,key)
          if distance < current_min:
            result = candidate
            current_min = distance
            
          # And add this node to the list of running nearest neighbors
          if distance < max(k_nearest, key=itemgetter('distance')):
            new_min = {'node': candidate, 
                       'distance': distance}
            self.insert_min(new_min, k_nearest, k) 
  
    else:
      # Otherwise we only have to check one branch
      candidate = None
      if key[self.axis] < self.key[self.axis]:
        
        if self.left_child:
          candidate = self.left_child.find_k_nearest(key, current_min, k_nearest, k, stats)
          
      else:
        if self.right_child:
          candidate = self.right_child.find_k_nearest(key, current_min, k_nearest, k, stats)
        
      if candidate:
        result = candidate  
    
    # Returning the minimum node found here, of if None if we found no minimum better than
    # the current running minimum
    return result
      
  def insert_min(self, new_min, min_list, k):
    """ Function which inserts a new nearest neighbor into the list of 
        nearest neighbors, ejecting the maximum value if necessary
        to keep the list size at k.
    """
    
    # First make sure it's not already in the list.
    if new_min not in min_list:
    
      # If adding the new item to the list will result in k items or less,
      # just insert it.
      if len(min_list) < k:
        min_list.append(new_min)
      else:
        
        # Find the item with the maximum distance
        max_item = max(min_list, key=itemgetter('distance'))
        max_index = min_list.index(max_item)
        # And replace it with the new minimum item
        min_list[max_index] = new_min
      
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
  
  @staticmethod  
  def distance(first_key, second_key):
    """ Calculates the squared distance between two points.
        Since we are only using it for comparison we can save
        the time to calculate the square root.
    """
    
    x_diff = first_key['x'] - second_key['x']
    y_diff = first_key['y'] - second_key['y']
    distance = (x_diff * x_diff) + (y_diff * y_diff)
    
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

  def nearest(self, key):
    return self.root.nearest(key)
  
  def k_nearest(self, key, k):
    return self.root.k_nearest(key, k)
  
  def search(self, key):
    return self.root.search(key)
  
  def check_balance(self, key):
    """ Function to check how balanced the tree is. 
        Should return something like the greatest differences in # nodes on one side vs.
        another?? """
    pass
  
  def print_tree(self):
    self.root.print_tree()  

  