import re

'''

a few json, text processing and other functions

'''

"""XPath-like JSON node traversal (using dot notation)
"""
def jpath(path,i):
  tmp=i
  for step in path.split('.'):
    if step not in tmp:
      return None
    tmp=tmp[step]
  return tmp

""" Coalesce: Return the first non-null value
"""
def nvl(x,y=''):
  if x is None:
    return y
  else:
    return x

chunker=re.compile(r'([^\w\$]+)')
whitespace=re.compile(r'\s+')

""" Chunk text into a list of words
"""
def chunk(x):
  result=tuple()
  chunks=chunker.split(x)
  for i in range(len(chunks)):
    if i%2:
      result+=(re.sub(whitespace,'',chunks[i]),)
    else:
      result+=(chunks[i],)
  return result

""" Generate ngrams of size n from a text string x
"""
def ngrams(n,x):
  result=list()
  chunks=chunk(x)
  #print chunks
  for i in range(0,len(chunks)-int(2*(n-1)),2):
    tmp=tuple(chunks[i:i+int(2*n-1)])
    if len(tmp[0])>0 and len(tmp[-1])>0: #first/last element could be zero length if content begins or ends with punctuation mark
      result.append(tmp)
  return result 

""" Check if all the elements from a list are contained in another list
"""
def contains(big,small,step=1): # both are lists
  lensmall=len(small)
  for i in xrange(0,len(big)-len(small)+1,step):
    for j in xrange(lensmall):
      if big[i+j]!=small[j]:
        break
    else: #for...else: else only executed on completing the loop; not on break
      return True
  return False

""" Takes list of numbers and checks if all are zero
"""
def all_zeroes(x):
  for i in x:
    if i>0:
      return False
  else:
    return True

""" Check if 
""" 
def has_subsequence(seq,query):
  idx=0
  for q in query:
    for i,v in enumerate(seq[idx:]):
      if v==q:
        idx=i+1
        break
    else:
      return False
  return True
