from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from core.files import handle_attachment,handle_file_update,handle_attachment,handle_file
from core import models, log, logic as core_logic
from core import forms as core_forms
from core.decorators import is_editor, is_book_editor, is_book_editor_or_author
from workflow import logic as workflow_logic
from editor import logic
from revisions import models as revision_models
from review import models as review_models
from manager import models as manager_models
from submission import forms as submission_forms
from editor import forms


@is_editor
def editor_dashboard(request):

	if request.POST:
		order = request.POST.get('order')
		filterby = request.POST.get('filter')
		search = request.POST.get('search')
	else:
		filterby = None
		search = None
		order = 'title'

	query_list = []

	if filterby:
		query_list.append(Q(stage__current_stage=filterby))

	if search:
		query_list.append(Q(title__contains=search) | Q(subtitle__contains=search) | Q(prefix__contains=search))

	if filterby:
		book_list = models.Book.objects.filter(publication_date__isnull=True).filter(*query_list).exclude(stage__current_stage='declined').order_by(order)
	else:
		book_list = models.Book.objects.filter(publication_date__isnull=True).exclude(stage__current_stage='declined').order_by(order)

	template = 'editor/dashboard.html'
	context = {
		'book_list': book_list,
		'recent_activity': models.Log.objects.all().order_by('-date_logged')[:15],
		'notifications': models.Task.objects.filter(assignee=request.user, completed__isnull=True).order_by('due'),
		'order': order,
		'filterby': filterby,
	}

	return render(request, template, context)


@is_book_editor
def editor_submission(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if request.POST and 'review' in request.POST:
		workflow_logic.create_new_review_round(book)
		book.stage.review = timezone.now()
		book.stage.current_stage = 'review'
		book.stage.save()

		if book.stage.current_stage == 'review':
			log.add_log_entry(book=book, user=request.user, kind='review', message='Submission moved to Review', short_name='Submission in Review')

		messages.add_message(request, messages.SUCCESS, 'Submission has been moved to the review stage.')

		return redirect(reverse('editor_review', kwargs={'submission_id': book.id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
		'author_include': 'editor/submission_details.html',
		'submission_files': 'editor/submission_files.html'
	}

	return render(request, template, context)

@is_book_editor
def editor_tasks(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	tasks = logic.get_submission_tasks(book, request.user)

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
		'author_include': 'shared/tasks.html',
		'tasks': tasks,
	}

	return render(request, template, context)

@is_book_editor
def editor_review(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	review_rounds = models.ReviewRound.objects.filter(book=book).order_by('-round_number')

	if request.POST and 'new_round' in request.POST:
		new_round = logic.create_new_review_round(book)
		return redirect(reverse('editor_review_round', kwargs={'submission_id': submission_id, 'round_number': new_round.round_number}))
	elif request.POST and 'move_to_editing' in request.POST:
		if not book.stage.editing:
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Submission moved to Editing.', short_name='Submission in Editing')
		book.stage.editing = timezone.now()
		book.stage.current_stage = 'editing'
		book.stage.save()
		return redirect(reverse('editor_editing', kwargs={'submission_id': submission_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'author_include': 'editor/review_revisions.html',
		'review_rounds': review_rounds,
		'revision_requests': revision_models.Revision.objects.filter(book=book, revision_type='review')
	}

	return render(request, template, context)

@is_book_editor
def editor_review_round(request, submission_id, round_number):
	book = get_object_or_404(models.Book, pk=submission_id)
	review_round = get_object_or_404(models.ReviewRound, book=book, round_number=round_number)
	reviews = models.ReviewAssignment.objects.filter(book=book, review_round__book=book, review_round__round_number=round_number)

	review_rounds = models.ReviewRound.objects.filter(book=book).order_by('-round_number')
	internal_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='internal', review_round__round_number=round_number).select_related('user', 'review_round')
	external_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='external', review_round__round_number=round_number).select_related('user', 'review_round')

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'author_include': 'editor/review_revisions.html',
		'submission_files': 'editor/view_review_round.html',
		'review_round': review_round,
		'review_rounds': review_rounds,
		'round_id': round_number,
		'revision_requests': revision_models.Revision.objects.filter(book=book, revision_type='review'),
		'internal_review_assignments': internal_review_assignments,
		'external_review_assignments': external_review_assignments,
	}

	return render(request, template, context)

@is_book_editor
def add_review_files(request, submission_id, review_type):
	submission = get_object_or_404(models.Book, pk=submission_id)

	if request.POST:
		files = models.File.objects.filter(pk__in=request.POST.getlist('file'))
		for file in files:
			if review_type == 'internal':
				submission.internal_review_files.add(file)
			else:
				submission.external_review_files.add(file)

		messages.add_message(request, messages.SUCCESS, '%s files added to Review' % files.count())

		return redirect(reverse('editor_review_round', kwargs={'submission_id': submission_id, 'round_number': submission.get_latest_review_round()}))

	template = 'editor/add_review_files.html'
	context = {
		'submission': submission,
	}

	return render(request, template, context)

@is_book_editor
def editor_add_reviewers(request, submission_id, review_type, round_number):

	submission = get_object_or_404(models.Book, pk=submission_id)
	reviewers = models.User.objects.filter(profile__roles__slug='reviewer')
	review_forms = review_models.Form.objects.all()
	committees = manager_models.Group.objects.filter(group_type='review_committee')
	review_round = get_object_or_404(models.ReviewRound, book=submission, round_number=round_number)

	if request.POST:
		reviewers = User.objects.filter(pk__in=request.POST.getlist('reviewer'))
		committees = manager_models.Group.objects.filter(pk__in=request.POST.getlist('committee'))
		review_form = review_models.Form.objects.get(ref=request.POST.get('review_form'))
		due_date = request.POST.get('due_date')
		email_text = request.POST.get('message')

		if request.FILES.get('attachment'):
			attachment = handle_file(request.FILES.get('attachment'), submission, 'misc', request.user)
		else:
			attachment = None

		# Handle reviewers
		for reviewer in reviewers:
			logic.handle_review_assignment(submission, reviewer, review_type, due_date, review_round, request.user, email_text, attachment)

		# Handle committees
		for committee in committees:
			members = manager_models.GroupMembership.objects.filter(group=committee)
			for member in members:
				logic.handle_review_assignment(submission, member.user, review_type, due_date, review_round, request.user, email_text, attachment)

		# Tidy up and save
		if review_type == 'internal' and not submission.stage.internal_review:
			submission.stage.internal_review = timezone.now()
			submission.stage.save()
			log.add_log_entry(book=submission, user=request.user, kind='review', message='Internal Review Started', short_name='Submission entered Internal Review')

		elif review_type == 'external' and not submission.stage.external_review:
			submission.stage.external_review = timezone.now()
			submission.stage.save()
			log.add_log_entry(book=submission, user=request.user, kind='review', message='External Review Started', short_name='Submission entered External Review')

		submission.review_form = review_form
		submission.save()

		return redirect(reverse('editor_review_round', kwargs={'submission_id': submission_id, 'round_number': submission.get_latest_review_round()}))

	template = 'editor/add_reviewers.html'
	context = {
		'reviewers': reviewers,
		'committees': committees,
		'active': 'new',
		'email_text': models.Setting.objects.get(group__name='email', name='review_request'),
		'review_forms': review_forms,
		'submission': submission,
	}

	return render(request, template, context)

@is_book_editor
def editor_review_assignment(request, submission_id, round_id, review_id):

	submission = get_object_or_404(models.Book, pk=submission_id)
	review_assignment = get_object_or_404(models.ReviewAssignment, pk=review_id)
	review_rounds = models.ReviewRound.objects.filter(book=submission).order_by('-round_number')
	result = review_assignment.results
	relations = review_models.FormElementsRelationship.objects.filter(form=result.form)
	data_ordered = workflow_logic.order_data(workflow_logic.decode_json(result.data), relations)

	template = 'editor/submission.html'
	context = {
		'author_include': 'editor/review_revisions.html',
		'submission_files': 'shared/view_review.html',
		'submission': submission,
		'review': review_assignment,
		'data_ordered': data_ordered,
		'result': result,
		'active': 'review',
		'review_rounds': review_rounds,
		'revision_requests': revision_models.Revision.objects.filter(book=submission, revision_type='review'),
	}

	return render(request, template, context)

@is_book_editor
def editor_editing(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if request.POST and request.GET.get('start', None):
		action = request.GET.get('start')

		if action == 'copyediting':
			book.stage.copyediting = timezone.now()
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Copyediting has commenced.', short_name='Copyediting Started')
		elif action == 'indexing':
			book.stage.indexing = timezone.now()
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Indexing has commenced.', short_name='Indexing Started')
		elif action == 'production':
			book.stage.production = timezone.now()
			book.stage.current_stage = 'production'
			log.add_log_entry(book=book, user=request.user, kind='production', message='Submission moved to Production', short_name='Submission in Production')
			book.stage.save()
			return redirect(reverse('editor_production', kwargs={'submission_id': submission_id}))

		book.stage.save()
		return redirect(reverse('editor_editing', kwargs={'submission_id': submission_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'author_include': 'editor/editing.html',
	}

	return render(request, template, context)

@is_book_editor
def editor_production(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if request.POST and request.GET.get('start', None):
		if request.GET.get('start') == 'typesetting':
			book.stage.typesetting = timezone.now()
			book.stage.save()

	template = 'editor/submission.html'
	context = {
		'author_include': 'editor/production/view.html',
		'active': 'production',
		'submission': book,
		'format_list': models.Format.objects.filter(book=book).select_related('file'),
		'chapter_list': models.Chapter.objects.filter(book=book).select_related('file'),
	}

	return render(request, template, context)

@is_book_editor
def catalog(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	internal_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='internal', completed__isnull=False).select_related('user', 'review_round')
	external_review_assignments = models.ReviewAssignment.objects.filter(book=book, review_type='external', completed__isnull=False).select_related('user', 'review_round')

	metadata_form = forms.EditMetadata(instance=book)
	cover_form = forms.CoverForm(instance=book)

	if request.POST:
		if request.GET.get('metadata', None):
			metadata_form = forms.EditMetadata(request.POST, instance=book)

			if metadata_form.is_valid():
				metadata_form.save()

				for keyword in book.keywords.all():
					book.keywords.remove(keyword)

				for keyword in request.POST.getlist('tags'):
					new_keyword, c = models.Keyword.objects.get_or_create(name=keyword)
					book.keywords.add(new_keyword)
				book.save()
				return redirect(reverse('catalog', kwargs={'submission_id': submission_id}))

		if request.GET.get('cover', None):
			cover_form = forms.CoverForm(request.POST, request.FILES, instance=book)

			if cover_form.is_valid():
				cover_form.save()
				return redirect(reverse('catalog', kwargs={'submission_id': submission_id}))

	template = 'editor/catalog/catalog.html' 
	context = {
		'active': 'production',
		'submission': book,
		'metadata_form': metadata_form,
		'cover_form': cover_form,
		'internal_review_assignments': internal_review_assignments,
		'external_review_assignments': external_review_assignments,
	}

	return render(request, template, context)

@is_book_editor
def identifiers(request, submission_id, identifier_id=None):
	book = get_object_or_404(models.Book, pk=submission_id)

	if identifier_id:
		identifier = get_object_or_404(models.Identifier, pk=identifier_id)

		if request.GET.get('delete', None) == 'true':
			identifier.delete()
			return redirect(reverse('identifiers', kwargs={'submission_id': submission_id}))

		form = forms.IdentifierForm(instance=identifier)
	else:
		identifier = None
		form = forms.IdentifierForm()

	if request.POST:
		if identifier_id:
			form = forms.IdentifierForm(request.POST, instance=identifier)
		else:
			form = forms.IdentifierForm(request.POST)

		if form.is_valid():
			new_identifier = form.save(commit=False)
			new_identifier.book = book
			new_identifier.save()

			return redirect(reverse('identifiers', kwargs={'submission_id': submission_id}))

	template = 'editor/catalog/identifiers.html'
	context = {
		'submission': book,
		'identifier': identifier,
		'form': form,
	}

	return render(request, template, context)

@is_book_editor
def update_contributor(request, submission_id, contributor_type, contributor_id=None):
	book = get_object_or_404(models.Book, pk=submission_id)

	if contributor_id:
		if contributor_type == 'author':
			contributor = get_object_or_404(models.Author, pk=contributor_id)
			form = submission_forms.AuthorForm(instance=contributor)
		elif contributor_type == 'editor':
			contributor = get_object_or_404(models.Editor, pk=contributor_id)
			form = submission_forms.EditorForm(instance=contributor)
	else:
		contributor = None
		if contributor_type == 'author':
			form = submission_forms.AuthorForm()
		elif contributor_type == 'editor':
			form = submission_forms.EditorForm()


	if request.POST:
		if contributor:
			if contributor_type == 'author':
				form = submission_forms.AuthorForm(request.POST, instance=contributor)
			elif contributor_type == 'editor':
				form = submission_forms.EditorForm(request.POST, instance=contributor)
		else:
			if contributor_type == 'author':
				form = submission_forms.AuthorForm(request.POST)
			elif contributor_type == 'editor':
				form = submission_forms.EditorForm(request.POST)

		if form.is_valid():
			saved_contributor = form.save()

			if not contributor:
				if contributor_type == 'author':
					book.author.add(saved_contributor)
				elif contributor_type == 'editor':
					book.editor.add(saved_contributor)

		return redirect(reverse('catalog', kwargs={'submission_id': submission_id}))

	template = 'editor/catalog/update_contributor.html'
	context = {
		'submission': book,
		'form': form,
		'contributor': contributor,
	}

	return render(request, template, context)

@is_book_editor
def delete_contributor(request, submission_id, contributor_type, contributor_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if contributor_id:
		if contributor_type == 'author':
			contributor = get_object_or_404(models.Author, pk=contributor_id)
		elif contributor_type == 'editor':
			contributor = get_object_or_404(models.Editor, pk=contributor_id)

		contributor.delete()

		return redirect(reverse('catalog', kwargs={'submission_id': submission_id}))

@is_book_editor
def add_format(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	format_form = forms.FormatForm()

	if request.POST:
		format_form = forms.FormatForm(request.POST, request.FILES)
		if format_form.is_valid():
			new_file = handle_file(request.FILES.get('format_file'), book, 'format', request.user)
			new_format = format_form.save(commit=False)
			new_format.book = book
			new_format.file = new_file
			new_format.save()
			log.add_log_entry(book=book, user=request.user, kind='production', message='%s %s loaded a new format, %s' % (request.user.first_name, request.user.last_name, new_format.identifier), short_name='New Format Loaded')
			return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

	template = 'editor/production/add_format.html'
	context = {
		'submission': book,
		'format_form': format_form,
	}

	return render(request, template, context)

@is_book_editor
def add_chapter(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	chapter_form = forms.ChapterForm()

	if request.POST:
		chapter_form = forms.ChapterForm(request.POST, request.FILES)
		if chapter_form.is_valid():
			new_file = handle_file(request.FILES.get('chapter_file'), book, 'chapter', request.user)
			new_chapter = chapter_form.save(commit=False)
			new_chapter.book = book
			new_chapter.file = new_file
			new_chapter.save()
			log.add_log_entry(book=book, user=request.user, kind='production', message='%s %s loaded a new chapter, %s' % (request.user.first_name, request.user.last_name, new_chapter.identifier), short_name='New Chapter Loaded')
			return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

	template = 'editor/production/add_chapter.html'
	context = {
		'submission': book,
		'chapter_form': chapter_form,
	}

	return render(request, template, context)

@is_book_editor
def delete_format_or_chapter(request, submission_id, format_or_chapter, id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if format_or_chapter == 'chapter':
		item = get_object_or_404(models.Chapter, pk=id)
	elif format_or_chapter == 'format':
		item = get_object_or_404(models.Format, pk=id)

	if item:
		item.file.delete()
		item.delete()
		messages.add_message(request, messages.SUCCESS, 'Item deleted')
	else:
		messages.add_message(request, messages.WARNING, 'Item not found.')

	return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

@is_book_editor
def update_format_or_chapter(request, submission_id, format_or_chapter, id):
	book = get_object_or_404(models.Book, pk=submission_id)

	if format_or_chapter == 'chapter':
		item = get_object_or_404(models.Chapter, pk=id)
	elif format_or_chapter == 'format':
		item = get_object_or_404(models.Format, pk=id)

	form = forms.UpdateChapterFormat()

	if request.POST:
		form = forms.UpdateChapterFormat(request.POST, request.FILES)
		if form.is_valid():
			item.name = request.POST.get('name')
			item.identifier = request.POST.get('identifier')
			item.save()
			if request.FILES:
				handle_file_update(request.FILES.get('file'), item.file, book, item.file.kind, request.user)
			return redirect(reverse('editor_production', kwargs={'submission_id': book.id}))

	template = 'editor/production/update.html'
	context = {
		'submission': book,
		'item': item,
		'form': form,
	}

	return render(request, template, context)

@is_book_editor
def assign_typesetter(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	typesetters = models.User.objects.filter(profile__roles__slug='typesetter')

	if request.POST:
		typesetter_list = User.objects.filter(pk__in=request.POST.getlist('typesetter'))
		file_list = models.File.objects.filter(pk__in=request.POST.getlist('file'))
		due_date = request.POST.get('due_date')
		email_text = request.POST.get('message')

		attachment = handle_attachment(request, book)

		for typesetter in typesetter_list:
			logic.handle_typeset_assignment(book, typesetter, file_list, due_date, email_text, requestor=request.user, attachment=attachment)

		return redirect(reverse('editor_production', kwargs={'submission_id': submission_id}))

	template = 'editor/submission.html'
	context = {
		'author_include': 'editor/production/view.html',
		'submission_files': 'editor/production/assign_typesetter.html',
		'active': 'production',
		'submission': book,
		'format_list': models.Format.objects.filter(book=book).select_related('file'),
		'chapter_list': models.Chapter.objects.filter(book=book).select_related('file'),
		'typesetters': typesetters,
	}

	return render(request, template, context)

@is_book_editor
def view_typesetter(request, submission_id, typeset_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	typeset = get_object_or_404(models.TypesetAssignment, pk=typeset_id)
	email_text = models.Setting.objects.get(group__name='email', name='author_typeset_request').value

	author_form = forms.TypesetAuthorInvite(instance=typeset)
	if typeset.editor_second_review:
		author_form = forms.TypesetTypesetterInvite(instance=typeset)
		email_text = models.Setting.objects.get(group__name='email', name='typesetter_typeset_request').value

	if request.POST and 'invite_author' in request.POST:
		if not typeset.completed:
			messages.add_message(request, messages.WARNING, 'This typeset has not been completed, you cannot invite the author to review.')
			return redirect(reverse('view_typesetter', kwargs={'submission_id': submission_id, 'typeset_id': typeset_id}))
		else:
			typeset.editor_review = timezone.now()
			typeset.save()

	elif request.POST and 'invite_typesetter' in request.POST:
		typeset.editor_second_review = timezone.now()
		typeset.save()
		return redirect(reverse('view_typesetter', kwargs={'submission_id': submission_id, 'typeset_id': typeset_id}))

	elif request.POST and 'send_invite_typesetter' in request.POST:
		author_form = forms.TypesetTypesetterInvite(request.POST, instance=typeset)
		if author_form.is_valid():
			author_form.save()
			typeset.typesetter_invited = timezone.now()
			typeset.save()
			email_text = request.POST.get('email_text')
			logic.send_invite_typesetter(book, typeset, email_text, request.user)
		return redirect(reverse('view_typesetter', kwargs={'submission_id': submission_id, 'typeset_id': typeset_id}))

	elif request.POST and 'send_invite_author' in request.POST:
		author_form = forms.TypesetAuthorInvite(request.POST, instance=typeset)
		if author_form.is_valid():
			author_form.save()
			typeset.author_invited = timezone.now()
			typeset.save()
			email_text = request.POST.get('email_text')
			logic.send_invite_typesetter(book, typeset, email_text, request.user)
		return redirect(reverse('view_typesetter', kwargs={'submission_id': submission_id, 'typeset_id': typeset_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'author_include': 'editor/production/view.html',
		'submission_files': 'editor/production/view_typeset.html',
		'active': 'production',
		'format_list': models.Format.objects.filter(book=book).select_related('file'),
		'chapter_list': models.Chapter.objects.filter(book=book).select_related('file'),
		'typeset': typeset,
		'author_form': author_form,
		'email_text': email_text,
	}

	return render(request, template, context)


@is_book_editor
def retailers(request, submission_id, retailer_id=None):
	book = get_object_or_404(models.Book, pk=submission_id)
	retailers = models.Retailer.objects.filter(book=book)
	form = forms.RetailerForm()

	if retailer_id:
		retailer = get_object_or_404(models.Retailer, pk=retailer_id)
		form = forms.RetailerForm(instance=retailer)

	if request.GET.get('delete', None):
		retailer.delete()
		return redirect(reverse('retailers', kwargs={'submission_id': submission_id}))

	if request.POST:
		if retailer_id:
			form = forms.RetailerForm(request.POST, instance=retailer)
			message = 'Retailer updated.'
		else:
			form = forms.RetailerForm(request.POST)
			message = 'New retailer added.'

		if form.is_valid():
			new_retailer = form.save(commit=False)
			new_retailer.book = book
			new_retailer.save()

			messages.add_message(request, messages.INFO, message)
			
			return redirect(reverse('retailers', kwargs={'submission_id': submission_id}))

	template = 'editor/catalog/retailers.html'
	context = {
		'submission': book,
		'retailers': retailers,
		'form': form,
		'retailer_id': retailer_id,
	}

	return render(request, template, context)

@is_book_editor
def decline_submission(request, submission_id):

	submission = get_object_or_404(models.Book, pk=submission_id)

	if request.POST and 'decline' in request.POST:
		submission.stage.declined = timezone.now()
		submission.stage.current_stage = 'declined'
		submission.stage.save()
		messages.add_message(request, messages.SUCCESS, 'Submission declined.')
		return redirect(reverse('editor_dashboard'))

	template = 'editor/decline_submission.html'
	context = {
		'submission': submission,
	}

	return render(request, template, context)

@is_book_editor
def delete_review_files(request, submission_id, review_type, file_id):
	submission = get_object_or_404(models.Book, pk=submission_id)
	file = get_object_or_404(models.File, pk=file_id)

	if review_type == 'internal':
		submission.internal_review_files.remove(file)
	else:
		submission.external_review_files.remove(file)

	return redirect(reverse('editor_review_round', kwargs={'submission_id': submission_id, 'round_number': submission.get_latest_review_round()}))

@is_book_editor
def editor_status(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'active': 'user_submission',
		'author_include': 'shared/status.html',
		'submission_files': 'shared/messages.html',
		'timeline': core_logic.build_time_line(book),
	}

	return render(request, template, context)

@is_book_editor
def assign_copyeditor(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	copyeditors = models.User.objects.filter(profile__roles__slug='copyeditor')

	if request.POST:
		copyeditor_list = User.objects.filter(pk__in=request.POST.getlist('copyeditor'))
		file_list = models.File.objects.filter(pk__in=request.POST.getlist('file'))
		due_date = request.POST.get('due_date')
		email_text = request.POST.get('message')

		attachment = handle_attachment(request, book)

		for copyeditor in copyeditor_list:
			logic.handle_copyeditor_assignment(book, copyeditor, file_list, due_date, email_text, requestor=request.user, attachment=attachment)
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Copyeditor %s %s assigend to %s' % (copyeditor.first_name, copyeditor.last_name, book.title), short_name='Copyeditor Assigned')

		return redirect(reverse('editor_editing', kwargs={'submission_id': submission_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'copyeditors': copyeditors,
		'author_include': 'editor/editing.html',
		'submission_files': 'editor/assign_copyeditor.html',
		'email_text': models.Setting.objects.get(group__name='email', name='copyedit_request'),
	}

	return render(request, template, context)

@is_book_editor
def view_copyedit(request, submission_id, copyedit_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id)
	author_form = core_forms.CopyeditAuthorInvite(instance=copyedit)
	email_text = models.Setting.objects.get(group__name='email', name='author_copyedit_request').value

	if request.POST and 'invite_author' in request.POST:
		if not copyedit.completed:
			messages.add_message(request, messages.WARNING, 'This copyedit has not been completed, you cannot invite the author to review.')
			return redirect(reverse('view_copyedit', kwargs={'submission_id': submission_id, 'copyedit_id': copyedit_id}))
		else:
			copyedit.editor_review = timezone.now()
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Copyedit Review Completed by %s %s' % (request.user.first_name, request.user.last_name), short_name='Editor Copyedit Review Complete')
			copyedit.save()

	elif request.POST and 'send_invite_author' in request.POST:

		attachment = handle_attachment(request, book)

		author_form = core_forms.CopyeditAuthorInvite(request.POST, instance=copyedit)
		author_form.save()
		copyedit.author_invited = timezone.now()
		copyedit.save()
		email_text = request.POST.get('email_text')
		logic.send_author_invite(book, copyedit, email_text, request.user, attachment)
		return redirect(reverse('view_copyedit', kwargs={'submission_id': submission_id, 'copyedit_id': copyedit_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'copyedit': copyedit,
		'author_form': author_form,
		'author_include': 'editor/editing.html',
		'submission_files': 'editor/view_copyedit.html',
		'email_text': email_text,
		'timeline': core_logic.build_time_line_editing_copyedit(copyedit),
	}

	return render(request, template, context)

@is_book_editor
def assign_indexer(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	indexers = models.User.objects.filter(profile__roles__slug='indexer')

	if request.POST:
		indexer_list = User.objects.filter(pk__in=request.POST.getlist('indexer'))
		file_list = models.File.objects.filter(pk__in=request.POST.getlist('file'))
		due_date = request.POST.get('due_date')
		email_text = request.POST.get('message')

		attachment = handle_attachment(request, book)

		for indexer in indexer_list:
			logic.handle_indexer_assignment(book, indexer, file_list, due_date, email_text, requestor=request.user, attachment=attachment)
			log.add_log_entry(book=book, user=request.user, kind='editing', message='Indexer %s %s assigend to %s' % (indexer.first_name, indexer.last_name, book.title), short_name='Indexer Assigned')

		return redirect(reverse('editor_editing', kwargs={'submission_id': submission_id}))

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'indexers': indexers,
		'author_include': 'editor/editing.html',
		'submission_files': 'editor/assign_indexer.html',
		'email_text': models.Setting.objects.get(group__name='email', name='index_request'),

	}

	return render(request, template, context)

@is_book_editor
def view_index(request, submission_id, index_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	index = get_object_or_404(models.IndexAssignment, pk=index_id)

	template = 'editor/submission.html'
	context = {
		'submission': book,
		'index': index,
		'author_include': 'editor/editing.html',
		'submission_files': 'editor/view_index.html',
		'timeline': core_logic.build_time_line_editing_indexer(index),

	}

	return render(request, template, context)

## CONTRACTS ##

@is_book_editor
def contract_manager(request, submission_id, contract_id=None):
	submission = get_object_or_404(models.Book, pk=submission_id)
	action = 'normal'
	if contract_id:
		new_contract_form = forms.UploadContract(instance=submission.contract)
		action = 'edit'
	else:
		new_contract_form = forms.UploadContract()

	if request.POST:
		if contract_id:
			new_contract_form = forms.UploadContract(request.POST, request.FILE, instance=submission.contract)
		else:
			new_contract_form = forms.UploadContract(request.POST, request.FILES)
		if new_contract_form.is_valid():
			new_contract = new_contract_form.save(commit=False)

			author_file = request.FILES.get('contract_file')
			new_file = handle_file(author_file, submission, 'contract', request.user)

			new_contract.editor_file = new_file
			new_contract.save()
			submission.contract = new_contract
			submission.save()

			if not new_contract.author_signed_off:
				email_text = models.Setting.objects.get(group__name='email', name='contract_author_sign_off').value
				logic.send_author_sign_off(submission, email_text, sender=request.user)

			if contract_id:
				_kwargs = {'submission_id': submission.id, 'contract_id': contract_id}
			else:
				_kwargs = {'submission_id': submission.id}

			return redirect(reverse('contract_manager', kwargs=_kwargs))

	template = 'editor/contract/contract_manager.html'
	context = {
		'submission': submission,
		'new_contract_form': new_contract_form,
		'action': action,
	}

	return render(request, template, context)

## END CONTRACTS ##
