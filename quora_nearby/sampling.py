import random
from operator import itemgetter

# Collection of functions to do sampling and generation of random 2D points
# Right now it uses a uniform distribution in a square, which is probably not
# really representative of topic map data, but you have to start somewhere.

def pop_median(data, sample_size, dimension):
  """ Removes the median from the list (based on the specified dimension),
      and returns it. 
  """
  # Get the median element
  median_index = get_median(data, sample_size, dimension)
  
  # Swap the median index with the last element of the list
  data[median_index], data[-1] = data[-1], data[median_index]
  
  # And pop the final element
  return data.pop()

def get_median(data, sample_size, dimension='x'):
  """ Function that estimates the median of the input list (data)
      by randomly selecting sample_size points from the list and 
      finding the median value of that set, based on the
      specified dimension (either 'x' or 'y').
      
      The input list (data) is expected to consist of dictionaries
      containing 'x' and 'y' keys, to represent points in space.
  """
  
  # If sample_size is 0 or bigger than size of the input data, just calculate the median 
  # directly on the whole list. This is mostly for testing right now.
  if sample_size == 0 or sample_size >= len(data):
    return calculate_median(data, dimension)
  
  # Otherwise use random sampling to estimate the median
  else:
    
      # Take a random sample of the list to cut down on input size
      sample_keys = get_samples(data, sample_size)

  # Convert the sample keys into a list of dictionaries with the value and
  # the index of the value in the original list (not the sample)  
  samples = []
  data_key = 'data'
  for key in sample_keys:
    sample = {}
    sample['key'] = key
    sample['x'] = data[key]['x']
    sample['y'] = data[key]['y']
    samples.append(sample)
  
  # Now find the median by finding the sample_size/2'th largest element
  # Just use selection sort until you have half the list done
  # This could be more clever for sure.
  iterations = sample_size / 2
  
  for i in range(iterations + 1):
    
    # Get the index of the minimum element in the unsorted region
    smallest = samples.index(min(samples[i:], key=itemgetter(dimension)))
    
    # Swap elements to put the min value at the end of the sorted range
    samples[smallest], samples[i] = samples[i], samples[smallest]
  
  """
  print("Sample of {} on a {}-item dataset:".format(sample_size, len(data)))  
  display_samples(samples)
  print("And the median on {} is: {}".format(dimension, samples[iterations]))
  print("which is at index {} in the original list.".format(samples[iterations]['key']))
  """
  
  # Return the index in the original data list of the sample's median value 
  # So, to access the actual median value you index into the data list
  return samples[iterations]['key']

def calculate_median(data, dimension='x'):
  """ Calculate the median directly by copying the input list, sorting,
      and return the middle element. """
  
  copy = data[:]
  copy.sort(key=itemgetter(dimension))
  
  median_index = len(copy) / 2
  
  return data.index(copy[median_index])

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

def get_samples(data, sample_size):
  """ Function to randomly sample the provided data, which is expected to be a list.
      sample_size specifies how many samples to return. There is no replacement, so
      each sample is guaranteed to be unique.
      
      The samples are actually selected by index, so you will need to index into the
      original list (data) to pull out the actual sample values. 
      
      Also, this function always returns a list, even if sample_size is 1. """
  
  # We are sampling with no replacement, so can't have 
  # the sample size greater than the size of the input list.
  if sample_size > len(data):
    raise ValueError("Sample size is greater than size of list to be sampled.")
  
  samples = []
  
  for sample in range(sample_size):
    
    # choose a random index in the list
    candidate = random.choice(range(len(data)))
    
    # try again if we get a duplicate
    while candidate in samples:
      candidate = random.choice(range(len(data)))
      
    samples.append(candidate)
  
  # Note that the samples returned are indexes into the original list,
  # not actual values.
  return samples
  
def display_samples(samples):
  """ Function to print a list of sample points to stdout for piping to
      a plotting program. """
  for sample in samples:
    print("{0[x]} {0[y]}".format(sample))

