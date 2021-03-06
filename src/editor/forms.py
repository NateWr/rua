from django import forms
from django.forms import ModelForm
from core import models as core_models
from revisions import models as revision_models
from editor import models

class RevisionForm(ModelForm):

	class Meta:
		model = revision_models.Revision
		fields = ('notes_from_editor', 'due')

class FormatForm(forms.ModelForm):

	format_file = forms.FileField(required=True)

	class Meta:
		model = core_models.Format
		exclude = ('book', 'file')

class ChapterForm(forms.ModelForm):

	chapter_file = forms.FileField(required=True)

	class Meta:
		model = core_models.Chapter
		exclude = ('book', 'file')

class PhysicalFormatForm(forms.ModelForm):

	class Meta:
		model = core_models.PhysicalFormat
		exclude = ('book',)

class UpdateChapterFormat(forms.Form):

	file = forms.FileField(required=False)
	identifier = forms.CharField(required=True)
	name = forms.CharField(required=True)

class UploadContract(forms.ModelForm):

	class Meta:
		model = core_models.Contract
		exclude = ('author_file',)

class AuthorContractSignoff(forms.ModelForm):

	class Meta:
		model = core_models.Contract
		fields = ('author_file',)



class EditMetadata(forms.ModelForm):

	class Meta:
		model = core_models.Book
		fields = (
			'prefix',
			'title',
			'subtitle',
			'series',
			'description',
			'license',
			'pages',
			'slug',
			'review_type',
			'languages',
			'publication_date'
		)

		widgets = {
            'languages': forms.CheckboxSelectMultiple(),
        }

class IdentifierForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		digital_format_choices = kwargs.pop('digital_format_choices', None)
		physical_format_choices = kwargs.pop('physical_format_choices', None)
		super(IdentifierForm, self).__init__(*args, **kwargs)
		if digital_format_choices and physical_format_choices:
			self.fields['digital_format'] = forms.ChoiceField(widget=forms.Select(), choices=digital_format_choices, required=False)
			self.fields['physical_format'] = forms.ChoiceField(widget=forms.Select(), choices=physical_format_choices, required=False)


	class Meta:
		model = core_models.Identifier
		fields = ('identifier', 'value', 'displayed', 'digital_format', 'physical_format',)

	def clean(self):
		digital_format = self.cleaned_data.get('digital_format')
		physical_format = self.cleaned_data.get('physical_format')

		if digital_format and physical_format:
			raise forms.ValidationError('You must select either a Digital Format, a Physical Format or Neither.')

class CoverForm(forms.ModelForm):

	class Meta:
		model = core_models.Book
		fields = ('cover',)

class RetailerForm(forms.ModelForm):

	class Meta:
		model = core_models.Retailer
		fields = ('name', 'link', 'price', 'enabled')

class Typeset(forms.ModelForm):

	class Meta:
		model = core_models.TypesetAssignment
		fields = ('note',)

class TypesetAuthorInvite(forms.ModelForm):

	class Meta:
		model = core_models.TypesetAssignment
		fields = ('note_to_author',)

class TypesetAuthor(forms.ModelForm):

	class Meta:
		model = core_models.TypesetAssignment
		fields = ('note_from_author',)

class TypesetTypesetterInvite(forms.ModelForm):

	class Meta:
		model = core_models.TypesetAssignment
		fields = ('note_to_typesetter',)


class TypesetTypesetter(forms.ModelForm):

	class Meta:
		model = core_models.TypesetAssignment
		fields = ('note_from_typesetter',)

class CoverImageReviewForm(forms.ModelForm):

	class Meta:
		model = models.CoverImageProof
		fields = ('note_to_author', )
