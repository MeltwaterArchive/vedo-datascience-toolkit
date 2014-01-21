import re

'''

a few json, text processing and other functions

'''

def jpath(path,i):
  tmp=i
  for step in path.split('.'):
    if step not in tmp:
      return None
    tmp=tmp[step]
  return tmp

def nvl(x,y=''):
  if x is None:
    return y
  else:
    return x

chunker=re.compile(r'([^\w\$]+)')
whitespace=re.compile(r'\s+')
def chunk(x):
  result=tuple()
  chunks=chunker.split(x)
  for i in range(len(chunks)):
    if i%2:
      result+=(re.sub(whitespace,'',chunks[i]),)
    else:
      result+=(chunks[i],)
  return result

def ngrams(n,x):
  result=list()
  chunks=chunk(x)
  #print chunks
  for i in range(0,len(chunks)-int(2*(n-1)),2):
    tmp=tuple(chunks[i:i+int(2*n-1)])
    if len(tmp[0])>0 and len(tmp[-1])>0: #first/last element could be zero length if content begins or ends with puncation mark
      result.append(tmp)
  return result 

def contains(big,small,step=1): # both are lists
  lensmall=len(small)
  for i in xrange(0,len(big)-len(small)+1,step):
    for j in xrange(lensmall):
      if big[i+j]!=small[j]:
        break
    else: #for...else: else only executed on completing the loop; not on break
      return True
  return False

def all_zeroes(x): # takes list of numbers and checks if all are zero
  for i in x:
    if i>0:
      return False
  else:
    return True

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
