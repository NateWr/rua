from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context, Template
from django.conf import settings

from core import models
from core import log

from pprint import pprint

def filepath(book, attachment):
	return '%s/%s/%s' % (settings.BOOK_DIR, book.id, attachment.uuid_filename)

def send_email(subject, context, from_email, to, html_template, bcc=None, cc=None, book=None, attachment=None):

	html_template.replace('\n', '<br />')

	htmly = Template(html_template)
	con = Context(context)
	html_content = htmly.render(con)

	if not type(to) in [list,tuple]:
		to = [to]

	msg = EmailMultiAlternatives(subject, html_content, from_email, to, bcc=bcc, cc=cc)
	
	if book:
		log.add_email_log_entry(book, subject, from_email, to,bcc,cc, html_content)
		
	msg.content_subtype = "html"

	if attachment:
		msg.attach_file(filepath(book, attachment))

	msg.send()

