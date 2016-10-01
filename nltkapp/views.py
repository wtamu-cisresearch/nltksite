from django.shortcuts import render
from .models import Document, Corpus
from django.http import JsonResponse
from django.conf import settings
import json
import os
import re
import nltk
from nltk.corpus import * 
from nltk.collocations import *
import string
import logging
logger = logging.getLogger('nltksite.nltkapp')

# Create your views here.
# this is horrible
def clearencoding(str):
	try:
		json.dumps(str)
		if len(str) == 1 and ord(str) > 128:
			logger.warn("Unicode Error on str='%s' code=%s Skipping" % (repr(str), ord(str)))
			str = ""
	except UnicodeDecodeError:
		logger.warn("Unicode Error on str='%s' code=%s Skipping" % (str, repr(str)))
		str = str.decode('utf8', 'ignore')
	
	return str
	
def index(request):
	logger.debug("index requested.")
	corpora = Corpus.objects.all()
	context = {'corpora': corpora}
	return render(request, 'nltkapp/index.html', context)
	
def sayhello(request):
	logger.debug("say hello.")
	return JsonResponse({'message': 'Hello World'})
	
def getdocuments(request):
	corpus_id = request.GET.get('corpus_id', None)
	c = Corpus.objects.get(pk=corpus_id)
	logger.debug("Getting list of documents for corpus %s (id=%s)" % (c.name,corpus_id))
	documents = c.document_set.all()
	documents_list = []
	for d in documents:
		documents_list.append({'id': d.id, 'name': d.file.name})
	return JsonResponse({'documents': documents_list})

def get_sentences(request):
	corpus_id = request.GET.get('corpus_id', None)
	document_ids = request.GET.get('document_ids', None)
	word = request.GET.get('word', None)
	logger.debug("corpus_id=%s, document_ids=%s, word=%s" % (corpus_id, str(document_ids), word))
	finalResult = {}
	
	corpus, internal_filter = open_corpus(corpus_id, document_ids)
	# \b is a word boundary match in regex, so we get government but not governmentally 
	pattern = "\\b" + word + "\\b"
	
	# Chosen corpus is an nltk internal corpus (gutenberg, bible, inaugural addresses, etc...).
	# We treat those slightly differently than user-mode corpora
	fileids = []
	if internal_filter:
		fileids = [internal_filter]
	else:
		# Get array of fileids used by the NLTK corpus object from our own document ids
		fileids = corpus.fileids()
		
	logger.debug("fileids=%s", fileids)
	for fileid in fileids:
		if fileid in corpus.fileids():
			sents = corpus.sents(fileid)
			results = []
			for sentence in sents:
				combined = clearencoding(' '.join(sentence))
				if re.search(pattern, combined):
					results.append(combined)
			if len(results) > 0:
				finalResult[fileid] = results
	
	# wdmatrix is a word-document matrix. finalResult['facebook.txt'] = [sentences]
	return JsonResponse({'word': word, 'wdmatrix':finalResult})
	
def wordfreq(request):
	corpus_id = request.GET.get('corpus_id', None)
	document_ids = json.loads(request.GET.get('document_ids', None))
	ngram = request.GET.get('ngram', None)
	scoring_method = request.GET.get('scoring_method', None)
	logger.debug("corpus_id=%s, document_ids=%s, ngram=%s, scoring_method=%s" % (corpus_id, str(document_ids), ngram, scoring_method))
	
	corpus, internal_filter = open_corpus(corpus_id, document_ids)
	if not internal_filter:
		words = corpus.words()
	else:
		words = corpus.words(internal_filter)
		
	logger.debug("PlaintextCorpusReader on files: %s" % corpus.fileids())
	
	if ngram == "1":
		return onegram_collocation(words)
	elif ngram == "2":
		first_word_list, fdist = bigram_collocation(words, scoring_method)
	elif ngram == "3":
		first_word_list, fdist = trigram_collocation(words, scoring_method)
	else:
		logger.debug("Invalid ngram value specified. " + ngram)
	
	word_list = []
	for b in first_word_list:
		for sample in fdist:
			if b == sample:
				worddict = {'word': clearencoding(' '.join(sample)), 'freq': fdist[sample], 'exclude': 0, 'exclude_reason': ''}
				break
		word_list.append(worddict)
		
	return JsonResponse({'list':word_list})
	
def onegram_collocation(words):
	fdist = nltk.FreqDist(words)
	unusual_list = unusual_words(words)
	word_list = []
	for sample in fdist:
		contains_punctuation = False
		all_punctuation = True
		for c in sample:
			if c in string.punctuation:
				contains_punctuation = True
			else:
				all_punctuation = False
		# If word contains punctuation OR occurs less than 3 times OR is a stop word, SKIP IT
		if (contains_punctuation or fdist[sample] < 3 or sample in stopwords.words('english')):
			continue
		
		if (clearencoding(sample.lower()) in unusual_list):
			unusual = True
		else:
			unusual = False
		
		if (len(clearencoding(sample)) > 0):
			word_list.append({'word': clearencoding(sample), 'freq': fdist[sample], 'exclude': 0, 'exclude_reason': '', 'unusual': unusual})

	return JsonResponse({'list':word_list})

def bigram_collocation(words, score):
	ignored_words = stopwords.words('english')
	bigrams = nltk.bigrams(words)
	fdist = nltk.FreqDist(bigrams)
	bigram_measures = nltk.collocations.BigramAssocMeasures()
	finder = BigramCollocationFinder.from_words(words)
	
	# Only select bigrams that appear at least 3 times
	finder.apply_freq_filter(3)
	finder.apply_word_filter(lambda w: len(w) < 3 or w.lower() in ignored_words)

	# return the 10 bigrams with the highest PMI
	method = bigram_measures.pmi
	if "student_t" in score:
		method = bigram_measures.student_t
	elif "chi_sq" in score:
		method = bigram_measures.chi_sq
	elif "pmi" in score:
		method = bigram_measures.pmi
	elif "likelihood_ratio" in score:
		method = bigram_measures.likelihood_ratio
	elif "poisson_stirling" in score:
		method = bigram_measures.poisson_stirling
	elif "jaccard" in score:
		method = bigram_measures.jaccard

	word_list = finder.nbest(method, 100)
	return [word_list, fdist] 
	
def trigram_collocation(words, score):
	ignored_words = stopwords.words('english')
	trigrams = nltk.trigrams(words)
	fdist = nltk.FreqDist(trigrams)
	trigram_measures = nltk.collocations.TrigramAssocMeasures()
	finder = TrigramCollocationFinder.from_words(words)
	#finder.apply_freq_filter(3)
	finder.apply_word_filter(lambda w: len(w) < 3 or w.lower() in ignored_words)
	
	method = trigram_measures.pmi
	if "student_t" in score:
		method = trigram_measures.student_t
	elif "chi_sq" in score:
		method = trigram_measures.chi_sq
	elif "pmi" in score:
		method = trigram_measures.pmi
	elif "likelihood_ratio" in score:
		method = trigram_measures.likelihood_ratio
	elif "poisson_stirling" in score:
		method = trigram_measures.poisson_stirling
	elif "jaccard" in score:
		method = trigram_measures.jaccard
	
	word_list = finder.nbest(method, 100)
	return [word_list, fdist]

# Given an array of words, connect to wordnet and return the part of speech, definition, etc...
def wordnet_data(request):
	words = request.GET.get('words', None)
	results = []
	for w in words:
		syns = wordnet.synsets(w)
		if len(syns) > 0:
			root_word = syns[0].lemmas[0].name
			pos = syns[0].pos
			definition = syns[0].definition
			synonyms = ''
			for syn in syns:
				if (syn.lemmas[0].name != root_word):
					synonyms += syn.lemmas[0].name + ', '
			
			examples = syns[0].examples
			results.append({'word': w,
					'root': root_word,
					'pos': pos,
					'definition': definition,
					'synonyms': synonyms[:-2],
					'examples': examples
			})
		else:
			results.append({'word': w,
					'root': 'undefined',
					'pos': 'undefined',
					'definition': 'undefined',
					'synonyms': 'undefined',
					'examples': 'undefined'
			})
	
	return JsonResponse({'results': results})
	
def unusual_words(text):
	text_vocab = set(w.lower() for w in text if w.isalpha())
	english_vocab = set(w.lower() for w in nltk.corpus.words.words())
	unusual = text_vocab.difference(english_vocab)
	return sorted(unusual)
	
def open_corpus(corpus_id, document_ids):
	c = Corpus.objects.get(pk=corpus_id)
	if c.internal_nltk_name:
		return eval(c.internal_nltk_name), c.internal_nltk_filter
	fileids = []
	for d in document_ids:
		d = int(d)
		# we want entire corpus
		if (d == -1):
			fileids = '.*\.txt'
			break
		document = Document.objects.get(pk=d)
		fileids.append(os.path.basename(document.file.name))
	# Kareem March 5, 2015: Added encoding=None. This prevents NLTK from assuming any specific encoding like utf8
	# Without encoding=None, we got UnicodeDecodeErrors. This avoids it, but we have to handle decoding ourselves now. We can try encoding="latin-1"
	return PlaintextCorpusReader(c.get_path(), fileids, encoding="latin-1"), ""