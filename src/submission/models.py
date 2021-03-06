from django.db import models
from django.contrib.auth.models import User

def proposal_status():
	return (
		('submission', 'Submission'),
		('revisions_required', 'Revisions Required'),
		('revisions_submitted', 'Revisions Submitted'),
		('accepted', 'Accepted'),
		('declined', 'Declined'),
	)

class Proposal(models.Model):


	owner = models.ForeignKey(User)
	title = models.CharField(max_length=255)
	subtitle = models.CharField(max_length=255)
	author = models.CharField(max_length=255)
	date_submitted = models.DateTimeField(auto_now_add=True)
	form = models.ForeignKey('core.ProposalForm')
	data = models.TextField()
	date_review_started = models.DateTimeField(blank=True, null=True)
	review_assignments = models.ManyToManyField('ProposalReview', related_name='review', null=True, blank=True)
	review_form = models.ForeignKey('review.Form', null=True, blank=True)

	status = models.CharField(max_length=20, choices=proposal_status(), default='submission')


class SubmissionChecklistItem(models.Model):

	slug = models.CharField(max_length=100)
	text = models.CharField(max_length=500)
	sequence = models.IntegerField(default=999)
	required = models.BooleanField(default=True)

	class Meta:
		ordering = ('sequence', 'text')

def review_recommendation():
	return (
		('accept', 'Accept'),
		('reject', 'Reject'),
		('revisions', 'Revisions Required')
	)

class ProposalReview(models.Model):
	proposal = models.ForeignKey(Proposal) #TODO: Remove this as it is already linked to the book through the review round
	user = models.ForeignKey(User)
	assigned = models.DateField(auto_now=True)
	accepted = models.DateField(blank=True, null=True)
	declined = models.DateField(blank=True, null=True)
	due = models.DateField(blank=True, null=True)
	completed = models.DateField(blank=True, null=True)
	files = models.ManyToManyField('core.File', blank=True, null=True)
	results = models.ForeignKey('review.FormResult', null=True, blank=True)
	recommendation = models.CharField(max_length=10, choices=review_recommendation(), null=True, blank=True)
	competing_interests = models.TextField(blank=True, null=True, help_text="If any of the authors or editors have any competing interests please add them here. EG. 'This study was paid for by corp xyz.'")

	class Meta:
		unique_together = ('proposal', 'user')

	def __unicode__(self):
		return u'%s - %s %s' % (self.pk, self.proposal.title, self.user.username)

	def __repr__(self):
		return u'%s - %s %s' %  (self.pk, self.proposal.title, self.user.username)
