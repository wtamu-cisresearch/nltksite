from django.conf.urls import patterns, include, url

urlpatterns = patterns('nltkapp.views',
	url(r'^$', 'index'),
)