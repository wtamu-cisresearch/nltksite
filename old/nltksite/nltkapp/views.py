# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from nltkapp.models import Document, Corpus

import logging
logger = logging.getLogger('nltksite.nltkapp')

def index(request):
	logger.debug("index requested.")
	corpora = Corpus.objects.all()
	return render_to_response('nltkapp/index.html', {'corpora': corpora}, context_instance=RequestContext(request))