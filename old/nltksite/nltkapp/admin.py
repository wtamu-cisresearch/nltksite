from nltkapp.models import Corpus, Document
from django.contrib import admin

class DocumentInline(admin.TabularInline):
	model = Document
	extra = 3

class CorpusAdmin(admin.ModelAdmin):
	inlines = [DocumentInline]
	
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document)