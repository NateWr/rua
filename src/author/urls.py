from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	# Review
	    url(r'dashboard/$', 'author.views.author_dashboard', name='author_dashboard'),
	    url(r'^submission/(?P<submission_id>\d+)/$', 'author.views.author_submission', name='author_submission'),
	    url(r'^submission/(?P<submission_id>\d+)/status/$', 'author.views.status', name='status'),
	    url(r'^submission/(?P<submission_id>\d+)/tasks/$', 'author.views.tasks', name='tasks'),

	    url(r'^submission/(?P<submission_id>\d+)/review/$', 'author.views.review', name='review'),
	    url(r'^submission/(?P<submission_id>\d+)/review/revisions/(?P<revision_id>\d+)/$', 'author.views.view_revisions', name='view_revisions'),
	    url(r'^submission/(?P<submission_id>\d+)/review/round/(?P<round_id>\d+)/$', 'author.views.view_review_round', name='view_review_round'),
	    url(r'^submission/(?P<submission_id>\d+)/review/round/(?P<round_id>\d+)/assignment/(?P<review_id>\d+)/$', 'author.views.view_review_assignment', name='view_review_assignment'),

		url(r'^submission/(?P<submission_id>\d+)/editing/$', 'author.views.editing', name='editing'),
		url(r'^submission/(?P<submission_id>\d+)/editing/view/copyeditor/(?P<copyedit_id>\d+)/$', 'author.views.view_copyedit', name='author_view_copyedit'),
		url(r'^submission/(?P<submission_id>\d+)/editing/view/indexer/(?P<index_id>\d+)/$', 'author.views.view_index', name='author_view_index'),
	    url(r'^submission/(?P<submission_id>\d+)/editing/copyedit/(?P<copyedit_id>\d+)/$', 'author.views.copyedit_review', name='copyedit_review'),
	    url(r'^submission/(?P<submission_id>\d+)/editing/typeset/(?P<typeset_id>\d+)/$', 'author.views.typeset_review', name='typeset_review'),
	    
	    url(r'^submission/(?P<submission_id>\d+)/production/$', 'author.views.author_production', name='author_production'),
	    url(r'^submission/(?P<submission_id>\d+)/production/view/typesetter/(?P<typeset_id>\d+)$', 'author.views.author_view_typesetter', name='author_view_typesetter'),

	    url(r'^submission/(?P<submission_id>\d+)/revisions/(?P<revision_id>\d+)/$', 'author.views.revision', name='author_revision'),
	    url(r'^submission/(?P<submission_id>\d+)/revisions/(?P<revision_id>\d+)/update_file/(?P<file_id>\d+)/$', 'author.views.revise_file', name='revise_file'),
	    url(r'^submission/(?P<submission_id>\d+)/contract/(?P<contract_id>\d+)/signoff/$', 'author.views.author_contract_signoff', name='author_contract_signoff'),
)
