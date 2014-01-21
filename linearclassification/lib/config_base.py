from linearclassification.lib.features import *

class ConfigBase:

  def __init__(self):
    pass

  featurepath='interaction.content'
  useunigrams=True
  usebigrams=True
  usetrigrams=True
  useorderedpairs=False
  useorderedtriples=False
  useorderedpairs=False

  useinteractionsource=False
  usewordpairs=False
  usenamewords=False
  useuserurlwords=False
  useshareurlwords=False

  usehashtags=False

  frequency_threshold=3
  keep_apriori_features=False
  nfeatures=500

  def stopwords(self):
    return ['the','que','for','with','this','los' ]
    #return ("the,this,and,can,here,there,for,from,with,more,is,you".split(',')) # |any "can"| is satisfied by "can't" !

  def apriori_features(self):
    features=set()
    return features

