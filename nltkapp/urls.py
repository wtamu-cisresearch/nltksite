from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^sayhello/$', views.sayhello, name='sayhello'),
	url(r'^getdocuments/$', views.getdocuments, name='getdocuments'),
	url(r'^wordfreq/$', views.wordfreq, name='wordfreq'),
]