from core import models
from core import email
from revisions import models as revision_models

from django.utils import timezone
from django.db.models import Q

from datetime import timedelta
from pprint import pprint

def remind_unaccepted_reviews(task):
	days = int(models.Setting.objects.get(group__name='cron', name='remind_unaccepted_reviews').value)
	email_text = models.Setting.objects.get(group__name='email', name='unaccepted_reminder').value
	dt = timezone.now()
	target_date = dt + timedelta(days=days)

	books = models.Book.objects.filter(stage__current_stage='review')

	for book in books:
		reviews = models.ReviewAssignment.objects.filter(book=book, review_round__round_number=book.get_latest_review_round(), unaccepted_reminder=False, accepted__isnull=True, declined__isnull=True, due=target_date.date)
		for review in reviews:
			send_reminder_email(book, 'Review Request Reminder', review, email_text)
			# Lets make sure that we don't accidentally send this twice.
			review.unaccepted_reminder = True
			review.save()

def remind_accepted_reviews(task):
	days = int(models.Setting.objects.get(group__name='cron', name='remind_accepted_reviews').value)
	email_text = models.Setting.objects.get(group__name='email', name='accepted_reminder').value
	dt = timezone.now()
	target_date = dt + timedelta(days=days)

	books = models.Book.objects.filter(stage__current_stage='review')

	for book in books:
		reviews = models.ReviewAssignment.objects.filter(book=book, review_round__round_number=book.get_latest_review_round(), accepted_reminder=False, accepted__isnull=False, completed__isnull=True, declined__isnull=True, due=target_date.date)
		for review in reviews:
			send_reminder_email(book, 'Review Request Reminder', review, email_text)
			# Lets make sure that we don't accidentally send this twice.
			review.accepted_reminder = True
			review.save()

def remind_overdue_reviews(task):
	days = int(models.Setting.objects.get(group__name='cron', name='remind_overdue_reviews').value)
	email_text = models.Setting.objects.get(group__name='email', name='overdue_reminder').value
	dt = timezone.now()
	target_date = dt - timedelta(days=days)

	books = models.Book.objects.filter(stage__current_stage='review')

	for book in books:
		reviews = models.ReviewAssignment.objects.filter(book=book, review_round__round_number=book.get_latest_review_round(), overdue_reminder=False, completed__isnull=True, declined__isnull=True, due=target_date.date)
		for review in reviews:
			send_reminder_email(book, 'Review Request Reminder', review, email_text)
			# Lets make sure that we don't accidentally send this twice.
			review.overdue_reminder = True
			review.save()

def reminder_overdue_revisions(task):
	days = int(models.Setting.objects.get(group__name='cron', name='revisions_reminder').value)
	email_text = models.Setting.objects.get(group__name='email', name='revisions_reminder_email').value
	dt = timezone.now()
	target_date = dt - timedelta(days=days)

	print target_date

	books = models.Book.objects.filter(Q(stage__current_stage='review') | Q(stage__current_stage='submission'))

	for book in books:
		revisions = revision_models.Revision.objects.filter(book=book, completed__isnull=True, overdue_reminder=False, due=target_date.date)
		for review in revisions:
			review.user = review.book.owner
			send_reminder_email(book, 'Revision Request Reminder', review, email_text)
			review.overdue_reminder = True
			review.save()

# Utils

def send_reminder_email(book, subject, review, email_text):
    from_email = models.Setting.objects.get(group__name='email', name='from_address')

    context = {
        'book': book,
        'review': review,
    }

    email.send_email(subject, context, from_email.value, review.user.email, email_text, book=book)
	
