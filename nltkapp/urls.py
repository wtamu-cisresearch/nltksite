from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^sayhello/$', views.sayhello, name='sayhello'),
	url(r'^getdocuments/$', views.getdocuments, name='getdocuments'),
	url(r'^wordfreq/$', views.wordfreq, name='wordfreq'),
	url(r'^get_sentences/$', views.get_sentences, name='get_sentences'),
	url(r'^wordnet_data/$', views.wordnet_data, name='wordnet_data'),
]