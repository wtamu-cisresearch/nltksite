from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.files import File
from django.conf import settings
import os
import errno
import logging
import zipfile
import tempfile
import sys
logger = logging.getLogger('nltksite.nltkapp')

# Create your models here.
def document_file_location(instance, filename):
	return '/'.join(["corpora", instance.corpus.name, filename])
	
class Corpus(models.Model):
	name = models.CharField(max_length=30)
	internal_nltk_name = models.CharField("Internal NLTK Corpus name (optional)", blank=True, help_text="Leave blank unless you are adding an NLTK built-in corpus, in which case, supply the name of the corpus.", max_length=15)
	internal_nltk_filter = models.CharField("Internal NLTK Corpus filter (optional)", blank=True, help_text="Used with Internal NLTK Corpus name if you want to filter the NLTK Corpus even further. Leave blank for default.", max_length=30)
	def get_path(self):
		# FIXME: settings.MEDIA_ROOT is relative. This could be an issue.
		return settings.MEDIA_ROOT + "/corpora/" + self.name
		
	def __str__(self):
		return self.name
	
	class Meta:
		verbose_name_plural = "Corpora"

class Document(models.Model):
	file = models.FileField(upload_to=document_file_location)
	corpus = models.ForeignKey(Corpus)
	
	def __str__(self):
		return self.file.name
		
@receiver(post_save, sender=Corpus)
def post_save_corpus_handler(sender, instance, **kwargs):
	logger.debug("Saving corpus %s" % instance.name)
	# FIXME: Handle changing the name of a corpus
	# FIXME: settings.MEDIA_ROOT is relative. This could be an issue.
	try:
		os.makedirs(instance.get_path())
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

@receiver(pre_delete, sender=Corpus)
def pre_delete_corpus_handler(sender, instance, **kwargs):
	# FIXME: Clean up directory and associated documents on corpus delete?
	logger.debug("Deleting corpus %s" % instance.name)
		
@receiver(post_save, sender=Document)
def post_save_document_handler(sender, instance, **kwargs):
	if instance.file.name is None:
		return
	logger.debug("Saving document %s" % instance.file.name)
	
	# Handle Zipped files
	full_path = settings.MEDIA_ROOT + "/" + instance.file.name
	try:
		if (zipfile.is_zipfile(full_path)):
			logger.debug("Document %s is a zip file. Unzipping contents." % full_path)
			z = zipfile.ZipFile(full_path)
			# Sometimes zip files include directories. Store their names here as we are unzipping
			# So we can clean them up and not make those directories into documents
			clean_dirs = []	
			for file in z.namelist():
				# Extract file to a temporary directory
				unzipped = z.extract(file, tempfile.gettempdir())
				if os.path.isdir(unzipped) == True:
					clean_dirs.append(unzipped)
				else:
					# Create document object for each file in the zip file.
					# This will upload it properly to our db
					document = Document()
					document.corpus = instance.corpus
					document.file.save(os.path.basename(unzipped), File(open(unzipped, 'r')))
					#document.save()
					os.remove(unzipped) # Remove temporary file
			
			# Clean up any directories created by unzipping
			while len(clean_dirs) > 0:
				os.rmdir(clean_dirs.pop())
			
			# Now just delete the Document object created for the initial zipfile
			instance.delete()
	except:
		logger.error('Error handling zip file.')
		
@receiver(pre_delete, sender=Document)
def pre_delete_document_handler(sender, instance, **kwargs):
	try:
		logger.debug('Deleting document %s' % (instance.file.name))
		instance.file.delete()
	except:
		logger.error('Error unlinking file: %s' % (sys.exc_info()[1]))