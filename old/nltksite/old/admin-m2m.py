from nltkapp.models import Corpus, Document
from django.contrib import admin

class DocumentAdmin(admin.ModelAdmin):
	filter_horizontal = ("corpora",)

class CorpusAdmin(admin.ModelAdmin):
	filter_horizontal = ("documents",)
		
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document, DocumentAdmin)