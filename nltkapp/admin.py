from django.contrib import admin
from .models import Corpus, Document

# Register your models here.
class DocumentInline(admin.TabularInline):
	model = Document
	extra = 3

class CorpusAdmin(admin.ModelAdmin):
	inlines = [DocumentInline]
	
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document)