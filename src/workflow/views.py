from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import logout as logout_user
from django.contrib.auth import login as login_user
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404, HttpResponse, StreamingHttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django import forms
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q


from django.conf import settings

from core import models
from core import forms
from core import log

from pprint import pprint
import os
import mimetypes
import mimetypes as mime
from uuid import uuid4

@login_required
def new_submissions(request):

	submission_list = models.Book.objects.filter(stage__current_stage='submission')

	template = 'workflow/new_submissions.html'
	context = {
		'submission_list': submission_list,
		'active': 'new',
	}

	return render(request, template, context)

@login_required
def view_new_submission(request, submission_id):

	submission = get_object_or_404(models.Book, pk=submission_id)

	template = 'workflow/view_new_submission.html'
	context = {
		'submission': submission,
		'active': 'new',
	}

	return render(request, template, context)

@login_required
def in_review(request):

	submission_list = models.Book.objects.filter(Q(stage__current_stage='i_review') | Q(stage__current_stage='e_review'))

	template = 'workflow/in_review.html'
	context = {
		'submission_list': submission_list,
		'active': 'review',
	}

	return render(request, template, context)

@login_required
def in_editing(request):

	submission_list = models.Book.objects.filter(Q(stage__current_stage='copy_editing') | Q(stage__current_stage='indexing'))

	template = 'workflow/in_editing.html'
	context = {
		'submission_list': submission_list,
		'active': 'editing',
	}

	return render(request, template, context)

@login_required
def in_production(request):

	submission_list = models.Book.objects.filter(stage__current_stage='production')

	template = 'workflow/in_production.html'
	context = {
		'submission_list': submission_list,
		'active': 'production',
	}

	return render(request, template, context)

# Log
@login_required
def view_log(request, submission_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	log_list = models.Log.objects.filter(book=book)

	template = 'workflow/log.html'
	context = {
		'submission': book,
		'log_list': log_list,
		'active': 'log',
	}

	return render(request, template, context)

# File Handlers - should this be in Core?
@login_required
def serve_file(request, submission_id, file_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	file_path = os.path.join(settings.BOOK_DIR, submission_id, _file.uuid_filename)

	try:
		fsock = open(file_path, 'r')
		mimetype = mimetypes.guess_type(file_path)
		response = StreamingHttpResponse(fsock, content_type=mimetype)
		response['Content-Disposition'] = "attachment; filename=%s" % (_file.uuid_filename)
		log.add_log_entry(book=book, user=request.user, kind='file', message='File %s downloaded.' % _file.uuid_filename, short_name='Download')
		return response
	except IOError:
		messages.add_message(request, messages.ERROR, 'File not found. %s/%s' % (file_path, _file.uuid_filename))
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def serve_versioned_file(request, submission_id, revision_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	versions_file = get_object_or_404(models.FileVersion, pk=revision_id)
	file_path = os.path.join(settings.BOOK_DIR, submission_id, versions_file.uuid_filename)

	try:
		fsock = open(file_path, 'r')
		mimetype = mimetypes.guess_type(file_path)
		response = StreamingHttpResponse(fsock, content_type=mimetype)
		response['Content-Disposition'] = "attachment; filename=%s" % (versions_file.uuid_filename)
		log.add_log_entry(book=book, user=request.user, kind='file', message='File %s downloaded.' % versions_file.uuid_filename, short_name='Download')
		return response
	except IOError:
		messages.add_message(request, messages.ERROR, 'File not found. %s/%s' % (file_path, versions_file.uuid_filename))
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def delete_file(request, submission_id, file_id, returner):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	file_id = _file.id
	_file.delete()

	if returner == 'new':
		return redirect(reverse('view_new_submission', kwargs={'submission_id': book.id}))

@login_required
def update_file(request, submission_id, file_id, returner):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)

	if request.POST:
		for file in request.FILES.getlist('update_file'):
			handle_file_update(file, _file, book, _file.kind)
			messages.add_message(request, messages.INFO, 'File updated.')

		if returner == 'new':
			return redirect(reverse('view_new_submission', kwargs={'submission_id': book.id}))

	template = 'workflow/update_file.html'
	context = {
		'submission': book,
		'file': _file,
	}

	return render(request, template, context)

@login_required
def versions_file(request, submission_id, file_id):
	book = get_object_or_404(models.Book, pk=submission_id)
	_file = get_object_or_404(models.File, pk=file_id)
	versions = models.FileVersion.objects.filter(file=_file)

	template = 'workflow/versions_file.html'
	context = {
		'submission': book,
		'file': _file,
		'versions': versions
	}

	return render(request, template, context)

## File helpers
def handle_file_update(file, old_file, book, kind):

	original_filename = str(file._get_name())
	filename = str(uuid4()) + '.' + str(original_filename.split('.')[1])
	folder_structure = os.path.join(settings.BASE_DIR, 'files', 'books', str(book.id))

	if not os.path.exists(folder_structure):
		os.makedirs(folder_structure)

	path = os.path.join(folder_structure, str(filename))
	fd = open(path, 'wb')
	for chunk in file.chunks():
		fd.write(chunk)
	fd.close()

	file_mime = mime.guess_type(filename)

	try:
		file_mime = file_mime[0]
	except IndexError:
		file_mime = 'unknown'


	new_version = models.FileVersion(
		file=old_file,
		original_filename=old_file.original_filename,
		uuid_filename=old_file.uuid_filename,
		date_uploaded=old_file.date_uploaded
	)

	new_version.save()

	old_file.mime_type=file_mime
	old_file.original_filename=original_filename
	old_file.uuid_filename=filename
	old_file.date_uploaded=timezone.now
	old_file.save()

	return path
