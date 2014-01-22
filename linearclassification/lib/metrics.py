from collections import defaultdict
import logging

def implode(x):
  return ','.join(map(str,x))

""" http://en.wikipedia.org/wiki/Confusion_matrix
"""
def confusion_matrix(list_of_pairs):
  freq=defaultdict(int)
  V=set()
  for l,r in list_of_pairs:
    V.add(l)
    V.add(r)
    freq[(l,r)]+=1

  V=sorted(V)
  logging.info(implode(["l/r"]+V))
  for l in V:
    logging.info(implode(["%s:" % str(l)]+[freq[(l,r)] for r in V]))

  agree=0
  disagree=0
  for l in V:
    for r in V:
      if l==r:
        agree+=freq[(l,r)]
      else:
        disagree+=freq[(l,r)]
  total=agree+disagree
  logging.info("agree=%i (%f pct); disagree=%i; total=%i",agree,float(agree)/total,disagree,total)


