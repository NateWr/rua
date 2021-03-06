from django import forms
from django.forms import ModelForm
from core import models

class Copyedit(forms.ModelForm):

	class Meta:
		model = models.CopyeditAssignment
		fields = ('note',)

class Typeset(forms.ModelForm):

	class Meta:
		model = models.TypesetAssignment
		fields = ('note_from_typesetter',)

class Index(forms.ModelForm):

	class Meta:
		model = models.IndexAssignment
		fields = ('note_from_indexer',)