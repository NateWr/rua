from core import models

def add_log_entry(book, user, kind, message, short_name):
	new_log_entry = models.Log(book=book, user=user, kind=kind, message=message, short_name=short_name)
	new_log_entry.save()
	return new_log_entry

def add_email_log_entry(book, subject, from_address, to, bcc, cc, content):
	log_dict = {
        'book': book,
        'subject': subject,
        'from_address':from_address,
        'to': to if to else '',
        'cc': cc if cc else '',
        'bcc': bcc if bcc else '',
        'content': content,
    }
	new_log_entry = models.EmailLog(**log_dict)
	new_log_entry.save()
	return new_log_entry