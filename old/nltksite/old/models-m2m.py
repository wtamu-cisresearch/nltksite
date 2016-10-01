from django.db import models

# Create your models here.

class Corpus(models.Model):
	name = models.CharField(max_length=30)
	documents = models.ManyToManyField('Document', blank=True)
	def __unicode__(self):
		return self.name
	
	class Meta:
		verbose_name_plural = "Corpora"
		
class Document(models.Model):
	file = models.FileField(upload_to='documents/')
	corpora = models.ManyToManyField(Corpus, through=Corpus.documents.through, blank=True)
	
	def __unicode__(self):
		return self.file.name