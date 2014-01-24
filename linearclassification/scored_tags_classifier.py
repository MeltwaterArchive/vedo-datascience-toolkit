import argparse,sys,re,json,imp,csv,logging,time,os
from collections import defaultdict
from sklearn.feature_selection import SelectKBest,chi2
from sklearn.naive_bayes import BernoulliNB
import numpy as np
from sklearn.linear_model import SGDClassifier

from lib.metrics import confusion_matrix
import itertools

from lib.features import *
from lib.utils import jpath,nvl,ngrams,all_zeroes,chunk

'''
Run as follows

  python scored_tags_classifier.py --test_period=4 --config_module_path=lib/user_type_config.py --training_csv=labels.csv --classpath=label \
    --training_json=1719749f2efeac6dddcbc79e3d6784bc_84191e72d3704c9f35e8

Write a set of tags to stdout

'''

# CONFIG

argparser=argparse.ArgumentParser(description='Train CSDL classifier on training data')
argparser.add_argument('--training_json',required=True,help='path to file containing full json description of all the training interactions')
argparser.add_argument('--classpath',required=True,help='path to class labels in json file or class label column name in csv')
argparser.add_argument('--test_period',required=True,type=int,help='how often to hold back training data for testing')
argparser.add_argument('--config_module_path',required=True,help='python module containing the configuration for the training')
argparser.add_argument('--training_csv',help='path to csv file containing labels (must have header )')

opts=argparser.parse_args()

logging.basicConfig(filename='.'.join(['scored_tags_classifier',time.strftime('%Y%m%d-%H%M%S'),str(os.getpid()),'log']),level=logging.DEBUG)
logging.info('command line options passed: %s',opts)

config=imp.load_source('config', opts.config_module_path).Config()
featurepath=config.featurepath
apriori_features=config.apriori_features()
stopwords=config.stopwords()
stopngrams=[chunk(x) for x in stopwords]


frequency_threshold=config.frequency_threshold # must see a feature at least this many times before including in the feature library
length_threshold=2 # word must be longer than this to be included as a feature

# CONSTANTS/FUNCTIONS #####################################################

wordsplitter=re.compile(r'[^\w\$]+')
whitespace=re.compile(r'\s+')
url_stopwords=set(['http','https','www','com'])

# retrieves the class label given an interaction id
intid2class=dict()
def get_class(interaction):
  if opts.training_csv is not None:
    intid=jpath('interaction.id',interaction)
    if intid in intid2class: # otherwise None is returned
      return intid2class[intid]
  else:
    c=jpath(opts.classpath,interaction)
    if isinstance(c,list): # eg if the class is set inside interaction.tags
      return c[0]
    else:
      return c

# associates an integer with each class label
classids=dict()
count_=1000 # arbitrary baseline
def get_classid(C):
  global count_
  if C not in classids:
    classids[C]=count_
    count_+=1
  return classids[C]

def get_classname(x):
  for classname,classid in classids.items():
    if classid==x:
      return classname

def build_feature_vectors(interactions,features,result):
  counter=0
  for interaction in interactions:
    counter+=1
    if not counter % 100:
      logging.debug("Working on interaction: %i",counter)
    fv=[int(f.is_satisfied_by(interaction)) for f in features]
    if all_zeroes(fv):
      pass
      #logging.info("Degenerate feature vector for interaction with id=%s",jpath('interaction.id',interaction))
    result.append(fv)

def report_confusion(interactions,targets,fvectors,title):
  logging.info("Confusion report for: %s",title)
  expectedvsactuals=zip(map(get_classname,targets),map(get_classname,clf.predict(fvectors)))
  confusion_matrix(expectedvsactuals)
  for i,(exp,act) in enumerate(expectedvsactuals):
    if exp!=act:
      logging.info("exp:act (%s,%s): %s |%s",exp,act, nvl(jpath(featurepath,interactions[i])),\
        '|'.join([selected_features[idx].string() for idx,satisfied in enumerate(fvectors[i]) if satisfied]))

def urldomain(url):
  domain=re.sub('https?://','',url)
  domain=re.sub('^www\d?\.','',domain)
  return domain.split('/')[0]

# MAIN #####################################################################################

#0 read in training file if supplied as csv
if opts.training_csv is not None:
  with open(opts.training_csv,'r') as f:
    reader=csv.DictReader(f)
    for row in reader:
      x=row[opts.classpath]
      if len(x)>0:
        intid2class[row['interaction.id']]=x
  logging.info("length of intid2class: %i",len(intid2class))

#1 read in interactions, creating the list of candidate aposteriori features based on words
ngramfreq=defaultdict(int) # term => frequency
wordpairfreq=defaultdict(int) # term => frequency
puncwordfreq=defaultdict(int) # term => frequency
namefreq=defaultdict(int)
userurltermfreq=defaultdict(int)
shareurltermfreq=defaultdict(int)
interactionsourcefreq=defaultdict(int)
combofreq=defaultdict(int)
hashtagfreq=defaultdict(int)
interactions=list()
targets=list()
test_interactions=list()
test_targets=list()
features=set()
with open(opts.training_json) as training_json:
  for ctr,i in enumerate(training_json):
    try:
      j=json.loads(i)
      C=get_class(j)
      if C is not None:

        if ctr % opts.test_period == 0:
          test_interactions.append(j)
          test_targets.append(get_classid(C))

        else:
          interactions.append(j)
          targets.append(get_classid(C))

          content=jpath(featurepath,j)
          if content is not None:
            content=content.lower()
            normalised_content=re.sub(r'(https?)://t.co/\w+','',content) #http://t.co/rerJLq49gl
            normalised_content=re.sub(r'@\w+','',normalised_content) # need to detect @mentions before chunking for unigrams!
            listofngrams=list()
            words=[w for w in wordsplitter.split(normalised_content) if w not in stopwords and len(w)>0]

            if config.useunigrams:
              listofngrams+=[(w,) for w in words]
            if config.usebigrams:
              listofngrams+=ngrams(2,content)
            if config.usetrigrams:
              listofngrams+=ngrams(3,content)
            for ngram in listofngrams:
              #if len(ngram)==1 and ngram[0] in stopwords: # ignore unigrams consisting of a stopword
              if ngram in stopngrams:
                continue
              #ignore ngrams that consist entirely of stopwords
              nstopwords=0
              for x in ngram:
                if x in stopwords:
                  nstopwords+=1
              if nstopwords==(len(ngram)+1)/2:
                continue
              if '@' in ngram: #ignore ngrams with @mentions
                continue
              # ignore ngrams that contains links, unless last chunk is http
              if len(ngram)>1 and ('http' in ngram[:-1] or 'https' in ngram[:-1]):
                continue
              ngramfreq[ngram]+=1
              if ngramfreq[ngram]==frequency_threshold and reduce(lambda x,y: x+len(y),ngram,0)>length_threshold: # only add if crossing the threshold
                features.add(NgramFeature(ngram,featurepath))

            for puncword in re.findall(r'\w+\s*(?:!|\?)',normalised_content): # strings like Thx! or Thx !
              puncword=re.sub(whitespace,'',puncword)
              puncwordfreq[puncword]+=1
              if puncwordfreq[puncword]==frequency_threshold:
                features.add(PunctuatedWordFeature(puncword,featurepath))

            # # word pairs
            if config.usewordpairs:
              for w in words:
                for x in words:
                  if w<x and len(w)>length_threshold and len(x)>length_threshold:
                    wordpairfreq[(w,x)]+=1
                    if wordpairfreq[(w,x)]==frequency_threshold:
                      features.add(WordPairFeature((w,x),featurepath))

            combos=set() # only add each combo once for each interaction
            comboterms=[w for w in WordComboFeature.split(normalised_content) if w not in stopwords]
            if config.useorderedpairs:
              combos.update(itertools.combinations(comboterms,2))
            if config.useorderedtriples:
              combos.update(itertools.combinations(comboterms,3))
            for combo in combos:
              combofreq[combo]+=1
              if combofreq[combo]==frequency_threshold:
                features.add(WordComboFeature(combo,featurepath))


          # other meta data paths #####################################

          if config.usenamewords: # words from names
            fullname=jpath('interaction.author.name',j)
            if fullname is not None:
              names=[n for n in wordsplitter.split(fullname)]
              for n in names:
                if len(n)>length_threshold:
                  namefreq[n]+=1
                  if namefreq[n]==3:
                    features.add(NgramFeature((n,),'interaction.author.name'))

          if config.useuserurlwords: # words from urls
            url=jpath('twitter.user.url',j)
            if url is not None:
              for t in wordsplitter.split(url):
                if len(t)>2 and t not in url_stopwords:
                  userurltermfreq[t]+=1
                  if userurltermfreq[t]==frequency_threshold:
                    features.add(NgramFeature((t,),'twitter.user.url'))

          if config.useshareurlwords: # words from urls
            urls=jpath('links.url',j)
            if isinstance(urls,list):
              for url in urls:
                if url is not None:
                  for t in wordsplitter.split(urldomain(url)):
                    if len(t)>2 and t not in url_stopwords:
                      shareurltermfreq[t]+=1
                      if shareurltermfreq[t]==frequency_threshold:
                        features.add(NgramFeature((t,),'links.url'))

          if config.useinteractionsource:
            source=jpath('interaction.source',j)
            if source is not None:
              interactionsourcefreq[source]+=1
              if interactionsourcefreq[source]==frequency_threshold:
                features.add(InFeature(source,'interaction.source'))

          if config.usehashtags:
            hashtags=jpath('interaction.hashtags',j)
            if hashtags is not None:
              for hashtag in hashtags:
                hashtagfreq[hashtag]+=1
                if hashtagfreq[hashtag]==frequency_threshold:
                  features.add(InFeature(hashtag,'interaction.hashtags'))

    except Exception, e:
      logging.warning("Exception! %s, %s", e,json.dumps(j))

features.update(apriori_features)
features=sorted(features,key=lambda x: x.string())
logging.info("Number of features %i; number of target classes %i",len(features),len(classids))

#2 build the feature vectors based on the candidate features

logging.info("Building training feature vectors")
fvectors=list()
build_feature_vectors(interactions,features,fvectors)


#3 run the feature selection ###################################################################################

selector=SelectKBest(chi2,k=nvl(config.nfeatures,'all'))
selector.fit(fvectors, targets)

# we need to build support index for selected features plus apriori features (as we want to over rule the selector on any apriori feature)
# first add in the idxs of the selected features:
support=set(selector.get_support(indices=True))
# next, add in the idx of all apriori features in case they were deselected
if config.keep_apriori_features:
  logging.info("Adding back in any deselected apriori features")
  for idx,f in enumerate(features):
    if f in apriori_features:
      support.add(idx)
support=sorted(support)
# now form the list of selected features
selected_features=[features[i] for i in support]
# and the projected features vectors for training set
fvectors2=list()
for fv in fvectors:
  fvectors2.append([fv[idx] for idx in support])

logging.info("Number of selected features %i",len(selected_features))
for f in selected_features:
  logging.info("Feature: %s",f.string().encode('utf-8','ignore'))

#4 learn ########################################################################

clf=SGDClassifier(shuffle=True,alpha=0.01,n_iter=50,fit_intercept=False)
clf.fit(fvectors2,targets)
logging.info("Classifier:%s",clf)

#5 report quality ########################################################################
report_confusion(interactions,targets,fvectors2,"training")
#build features vectors for test data
test_fvectors=list()
build_feature_vectors(test_interactions,selected_features,test_fvectors)
report_confusion(test_interactions,test_targets,test_fvectors,"test")

#6 write CSDL tags #############################################################################

coeffs=clf.coef_
if len(coeffs)==1: # binary case: coeffs are stored a little differently
  for fcount,feature in enumerate(selected_features):
    try:
      coeff=coeffs[0][fcount]
      print "tag.%s %f {%s}" % (get_classname(clf.classes_[1]),coeff,feature.to_csdl().encode('utf-8','ignore'))
      print "tag.%s %f {%s}" % (get_classname(clf.classes_[0]),-coeff,feature.to_csdl().encode('utf-8','ignore'))
    except Exception, e:
      print >>sys.stderr, e, feature.string()
else: # more than two classes
  for ccount,classid in enumerate(clf.classes_):
    for fcount,feature in enumerate(selected_features):
      try:
        tagcsdl="tag.%s %f {%s}" % (get_classname(classid),coeffs[ccount][fcount],feature.to_csdl())
        print tagcsdl.encode('utf-8','ignore')
      except Exception, e:
        print >>sys.stderr, e, feature.string()

