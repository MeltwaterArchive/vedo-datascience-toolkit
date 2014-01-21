import re,sys
from linearclassification.lib.utils import jpath,chunk,contains,has_subsequence

wordsplitter=re.compile(r'[^\w\$]+')


class Feature: # base class for shared behaviour - mainly hashability (to allow deduping of apriori and aposteriori features)
  def __hash__(self):
    return hash(self.string())
  def __eq__(self,other):
    return self.__hash__()==other.__hash__()
  def to_csdl(self):
    return "TODO!",self.string()

chunk_cache=dict() # for perf, as chunking is pretty slow!
class NgramFeature(Feature):
  def __init__(self,chunks,path):
    self.chunks=chunks
    self.path=path # i.e. path to the text field we're going to check for the word, eg interaction.content or links.title
    self.string_=''
    for chunk in chunks:
      if len(chunk)>0:
        self.string_+=chunk
      else:
        self.string_+=' '
  def is_satisfied_by(self,interaction):
    global chunk_cache
    text=jpath(self.path,interaction)
    if text is None:
      return False

    if not isinstance(text,list): # we need to handle the case when the path returns a list, eg for shareurls, so standardise on that
      text=[text]
    for t in text:
      t=t.lower()
      if t not in chunk_cache:
        chunk_cache[t]=chunk(t)
      if contains(chunk_cache[t],self.chunks,2):
        return True
    return False

  def string(self):
    return '%ig(%s)[%s]' % ((len(self.chunks)+1)/2,self.string_,self.path)
  def to_csdl(self):
      return '%s contains "%s"' % (self.path,self.string_)

class DisjoinedNgramsFeature(Feature):
  def __init__(self,phrases,path): #phrases is a list of chunks
    self.ngramfeatures=[NgramFeature(chunk(phrase),path) for phrase in phrases]
    self.path=path
  def is_satisfied_by(self,interaction):
    for f in self.ngramfeatures:
      if f.is_satisfied_by(interaction):
        return True
    return False
  def string(self):
    return ''.join([f.string() for f  in self.ngramfeatures])
  def to_csdl(self):
    return '%s any "%s"' % (self.path,','.join([f.string_ for f in self.ngramfeatures]))

# also uses chunk cache
class PunctuatedWordFeature(Feature):
  def __init__(self,word,path):
    self.word=word
    self.path=path
  def is_satisfied_by(self,interaction):
    global chunk_cache
    text=jpath(self.path,interaction)
    if text is None:
      return False
    else:
      text=text.lower()
      if text not in chunk_cache:
        chunk_cache[text]=chunk(text)
      return contains(chunk_cache[text],(self.word[:-1],self.word[-1]),2)
  def string(self):
    return "pw(%s)" % self.word
  def to_csdl(self):
    return '%s contains "%s"' % (self.path,self.word)

class SubstrFeature(Feature): # NB CASE SENSITIVE
  def __init__(self,chars,path):
    self.chars=chars
    self.path=path
  def is_satisfied_by(self,interaction):
    text=jpath(self.path,interaction)
    if text is None:
      return False
    else:
      return self.chars in text # NB CASE SENSITIVE
  def string(self):
    return "s(%s)" % self.chars
  def to_csdl(self):
    return '%s cs substr "%s"' % (self.path,self.chars)

class WordPairFeature(Feature):
  def __init__(self,pair,path):
    self.pair=pair
    self.path=path
  def is_satisfied_by(self,interaction):
    text=jpath(self.path,interaction)
    if text is None:
      return False
    else:
      words=wordsplitter.split(text.lower())
      (w,x)=self.pair
      return w in words and x in words
  def string(self):
    return 'p(%s,%s)' % self.pair
  def to_csdl(self):
    (w,x)=self.pair
    return '%s all "%s,%s"' % (self.path,w,x)

combosplitter=re.compile(r'([^\w\$])+')
comboignore=re.compile(r'[\s\,\.\#\']+')
combochars=re.compile(r'[\?\!]')
class WordComboFeature(Feature): # ordered combo of words
  def __init__(self,combo,path):
    self.combo=combo
    self.path=path
  def is_satisfied_by(self,interaction):
    text=jpath(self.path,interaction)
    if text is None:
      return False
    else:
      words=WordComboFeature.split(text.lower())
      return has_subsequence(words,self.combo)
  def string(self):
    return 'c%i(%s)' % (len(self.combo),str(self.combo))
  @classmethod
  def split(cls,text):
    result=[x for x in combosplitter.split(text) if not comboignore.match(x) and (len(x)>2 or combochars.search(x))]
    return result


class PathExistsFeature(Feature):
  def __init__(self,path):
    self.path=path
  def is_satisfied_by(self,interaction):
    return jpath(self.path,interaction) is not None
  def string(self):
    return "E[%s]" % self.path
  def to_csdl(self):
    return '%s exists' % (self.path)

class RegexFeature(Feature):
  def __init__(self,regex,path):
    self.regex=regex
    self.path=path
  def is_satisfied_by(self,interaction):
    text=jpath(self.path,interaction)
    if text is None:
      return False
    else:
      return re.search(self.regex,text) is not None
  def string(self):
    return "re(%s)" % self.regex
  def to_csdl(self):
    return '%s regex_partial "%s"' % (self.path,self.regex.replace('\\','\\\\'))

class InFeature(Feature):
  def __init__(self,term,path):
    self.term=term.lower()
    self.path=path
  def is_satisfied_by(self,interaction):
    text=jpath(self.path,interaction)
    if text is None:
      return False
    if not isinstance(text,list): # we need to handle the case when the path returns a list, eg for hashtags, so standardise on that
      text=[text]
    for t in text:
      t=t.lower()
      if self.term==t:
        return True
    return False

  def string(self):
    return "in(%s)" % self.term
  def to_csdl(self):
    return '%s in "%s"' % (self.path,self.term)


class BoolFeature(Feature):
  def __init__(self,val,path):
    self.val=val
    self.path=path
  def is_satisfied_by(self,interaction):
    x=jpath(self.path,interaction)
    if x is None:
      return False
    return x==self.val
  def string(self):
    return "bool(%s)" % self.val
  def to_csdl(self):
    return '%s == %s' % (self.path,1 if self.val else 0)
