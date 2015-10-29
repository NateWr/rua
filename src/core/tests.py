from django.test import TestCase
from core import models
from django.utils import timezone
import time
import datetime
from django.test import SimpleTestCase
from django.db.models import Q
from core import views
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve, reverse
from  __builtin__ import any as string_any
# Create your tests here.

class CoreTests(TestCase):

	# Dummy DBs
	fixtures = [
		'settinggroups',
		'settings',
		'langs',
		'cc-licenses',
		'role',
	]

	def setUp(self):
		self.client = Client(HTTP_HOST="testing")
		self.username = 'rua_user'
		self.email = 'fake.emaill@fakeaddress.com'
		self.password = 'rua_tester'
		self.user = User.objects.create_user(username=self.username, email=self.email,first_name="Rua",last_name="Testing", password=self.password)
		self.profile=models.Profile(user=self.user,institution="Testing",country="GB",department="test")
		self.profile.save()
		self.user.profile=self.profile
		self.user.save()

		login = self.client.login(username='rua_user', password='rua_tester')
		self.assertEqual(login, True)

	def tearDown(self):
		pass

	def test_set_up(self):
		"""
		testing set up
		"""
		self.assertEqual(self.user.username=="rua_user", True)
		self.assertEqual(self.user.email=="fake.emaill@fakeaddress.com", True)
		self.assertEqual(self.user.first_name=="Rua", True)
		self.assertEqual(self.user.last_name=="Testing", True)
		self.assertEqual(self.user.profile.institution=="Testing", True)
		self.assertEqual(self.user.profile.country=="GB", True)
		self.assertEqual(self.user.profile.department=="test", True)

##############################################	Fixture Tests	 ##############################################		

	def test_roles_fixture(self):
		"""
		testing roles fixture
		"""
		roles = ["Reader","Author","Copyeditor","Reviewer","Press Editor","Book Editor","Series Editor","Indexer","Typesetter"]
		roles_exist=True	
		for role_name in roles:
			try:
				role = models.Role.objects.get(name=role_name)
			except models.Role.DoesNotExist:
				roles_exist = False
		number_of_roles = len(models.Role.objects.all())
		self.assertEqual(number_of_roles==9, True)
		self.assertEqual(roles_exist, True)
	
	def test_settings_fixture(self):
		"""
		testing settings fixture
		"""
		settings = ["accronym","base_url","ci_required","city","copyedit_author_instructions","copyedit_instructions","description","footer","index_instructions","press_name","proposal_form","review_suggestions","submission_checklist_help","submission_guidelines","typeset_author_instructions","typeset_instructions","accepted_reminder","author_copyedit_request","author_submission_ack","author_typeset_request","contract_author_sign_off","copyedit_request","editor_submission_ack","external_review_request","from_address","index_request","overdue_reminder","proposal_accept","proposal_decline","proposal_request_revisions","proposal_review_request","request_revisions","review_request","revisions_reminder_email","typeset_request","typesetter_typeset_request","unaccepted_reminder","brand_header","favicon","remind_accepted_reviews","remind_overdue_reviews","remind_unaccepted_reviews","revisions_reminder"]
		settings_exist=True	
		for setting_name in settings:
			try:
				setting = models.Setting.objects.get(name=setting_name)
			except models.Setting.DoesNotExist:
				settings_exist = False
		number_of_settings = len(models.Setting.objects.all())
		self.assertEqual(number_of_settings==43, True)
		self.assertEqual(settings_exist, True)
	
	def test_setting_groups_fixture(self):
		"""
		testing setting groups fixture
		"""
		setting_groups = ["general","page","email","look","cron"]
		setting_groups_exist=True
		for group in setting_groups:
			try:
				group = models.SettingGroup.objects.get(name=group)
			except models.SettingGroup.DoesNotExist:
				setting_groups_exist = False
		number_of_setting_groups = len(models.SettingGroup.objects.all())
		self.assertEqual(number_of_setting_groups==5, True)
		self.assertEqual(setting_groups_exist, True)

	def test_cc_licenses_fixture(self):
		"""
		testing cc licenses fixture
		"""
		license_codes = ["cc-4-by","cc-4-by-sa","cc-4-by-nd","cc-4-by-nc","cc-4-by-nc-nd","cc-4-by-nd-sa"]
		license_codes_exist=True
		for code in license_codes:
			try:
				group = models.License.objects.get(code=code)
			except models.License.DoesNotExist:
				license_codes_exist = False
		number_of_licenses = len(models.License.objects.all())
		self.assertEqual(number_of_licenses==6, True)
		self.assertEqual(license_codes_exist, True)

	def test_langs_fixture(self):
		"""
		testing langs fixture
		"""
		langs= ["abk","afr","afa","amh","anp","apa","ara","hye","asm","ast","aus","aze","ban","bat","bas","bak","eus","bel","ben","ber","bos","bre","bul","mya","cat","cel","cai","che","chr","zho","cor","cos","hrv","ces","dak","dan","dum","nld","eng","est","fao","fij","fil","fin","fiu","fra","gla","car","glg","lug","gay","gba","gez","kat","deu","gmh","goh","gem","gil","hat","haw","heb","hin","hun","isl","ind","gle","ita","jpn","tlh","kon","kor","kur","kru","lat","lav","lit","nds","lus","ltz","mkd","mlg","msa","mal","mlt","mni","mri","myn","moh","mol","mon","new","nep","non","nai","nor","nno","pag","pan","paa","fas","phi","pol","por","ron","rom","rus","smo","sco","srp","iii","scn","sla","slk","slv","sog","som","son","wen","spa","zgh","suk","sun","swa","swe","gsw","syr","tha","tog","ton","tsi","tso","tsn","tum","tur","ukr","urd","uzb","vai","ven","vie","cym","yap","yid","zap","zha","zul"]
		langs_exist=True
		for lang in langs:
			try:
				language = models.Language.objects.get(code=lang)
			except models.Language.DoesNotExist:
				langs_exist = False
		number_of_langs = len(models.Language.objects.all())
		self.assertEqual(number_of_langs==147, True)
		self.assertEqual(langs_exist, True)

##############################################	Model Tests	 ##############################################		

	def test_author_model(self):
		"""
		test author model
		"""
		self.author = models.Author(
			first_name = "rua_first_name",
			last_name = "rua_last_name",
			salutation = "Mr",
			institution = "Testing",
			department = "test",
			country = "GB",
			author_email = "fake@fakeaddress.com"
			)
		self.author.save()
		#model functions
		fullname="%s %s" % ("rua_first_name","rua_last_name")
		unicode_text=u'%s - %s %s' % (str(1), "rua_first_name", "rua_last_name")
		self.assertEqual(self.author.__repr__()==unicode_text,True)
		self.assertEqual(self.author.__unicode__()==unicode_text,True)
		self.assertEqual(self.author.full_name()==fullname, True)
		
		#check that it exists in the database
		test_author=models.Author.objects.get(first_name="rua_first_name",last_name="rua_last_name",institution="Testing")
		self.assertEqual(test_author.first_name=="rua_first_name", True)
		self.assertEqual(test_author.last_name=="rua_last_name", True)
		self.assertEqual(test_author.salutation=="Mr", True)
		self.assertEqual(test_author.institution=="Testing", True)
		self.assertEqual(test_author.country=="GB", True)
		self.assertEqual(test_author.author_email=="fake@fakeaddress.com", True)
		self.assertEqual(test_author.department=="test", True)
		self.assertEqual(test_author.full_name()==fullname, True)
		
		#alter field
		self.author.first_name="rua_changed_first_name"
		self.author.save()

		self.assertEqual(self.author.first_name=="rua_changed_first_name", True)
		#check number of created objects
		self.assertEqual(len(models.Author.objects.all())==1, True)
	

	def test_add_role_to_user(self):
		roles = models.Role.objects.filter(name__icontains="Editor")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		for role in roles:
			found = False
			for saved_role in self.user.profile.roles.all():
				if cmp(role,saved_role)==0:
					found=True 
			self.assertEqual(found, True)

##############################################	View Tests	 ##############################################		

################### Dashboards ##################

	def test_editor_access(self):
		roles = models.Role.objects.filter(name__icontains="Editor")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		resp = self.client.get(reverse('editor_dashboard'))
	
		content =resp.content
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, False)
	
	def test_not_editor_access(self):
		resp = self.client.get(reverse('editor_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, True)

	def test_editor_redirect(self):
		roles = models.Role.objects.filter(name__icontains="Editor")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		response = self.client.get(reverse('user_dashboard'))
		self.assertRedirects(response, "http://testing/editor/dashboard/", status_code=302, target_status_code=200, host=None, msg_prefix='', fetch_redirect_response=True)
	
	def test_author_access(self):
		roles = models.Role.objects.filter(name__icontains="Author")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.last_login=timezone.now()
		self.user.save()
		self.user.profile.save()

		resp = self.client.get(reverse('author_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, False)

	def test_not_author_access(self):
		resp = self.client.get(reverse('author_dashboard'))
		content =resp.content
		self.user.last_login=timezone.now()
		self.user.save()

		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, True)

	def test_author_redirect(self):
		roles = models.Role.objects.filter(name__icontains="Author")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.last_login=timezone.now()	
		self.user.save()
		self.user.profile.save()
		response = self.client.get(reverse('user_dashboard'))
		self.assertRedirects(response, "http://testing/author/dashboard/", status_code=302, target_status_code=200, host=None, msg_prefix='', fetch_redirect_response=True)

	def test_onetasker_access(self):
		roles = models.Role.objects.filter(Q(name__icontains="Typesetter") | Q(name__icontains="Copyeditor") | Q(name__icontains="Indexer"))
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		resp = self.client.get(reverse('onetasker_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, False)

	def test_not_onetasker_access(self):
		resp = self.client.get(reverse('onetasker_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, True)

	def test_onetasker_redirect(self):
		roles = models.Role.objects.filter(Q(name__icontains="Typesetter") | Q(name__icontains="Copyeditor") | Q(name__icontains="Indexer"))
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		response = self.client.get(reverse('user_dashboard'))
		self.assertRedirects(response, "http://testing/tasks/", status_code=302, target_status_code=200, host=None, msg_prefix='', fetch_redirect_response=True)
	
	def test_reviewer_access(self):
		roles = models.Role.objects.filter(name__icontains="Reviewer")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		resp = self.client.get(reverse('reviewer_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, False)

	def test_not_reviewer_access(self):
		resp = self.client.get(reverse('reviewer_dashboard'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, True)

	def test_reviewer_redirect(self):
		roles = models.Role.objects.filter(name__icontains="Reviewer")
		for role in roles:
			self.user.profile.roles.add(role)
		self.user.save()
		self.user.profile.save()
		response = self.client.get(reverse('user_dashboard'))
		self.assertRedirects(response, "http://testing/review/dashboard/", status_code=302, target_status_code=200, host=None, msg_prefix='', fetch_redirect_response=True)

	def test_view_profile(self):
		resp = self.client.get(reverse('view_profile'))
		content =resp.content
		
		self.assertEqual(resp.status_code, 200)
		self.assertEqual("403" in content, False)
		self.assertEqual("500" in content, False)

	def test_logout(self):
		resp = self.client.get(reverse('logout'))
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp['Location'], "http://testing/")





##############################################	Form Tests	 ##############################################		


	def test_update_profile(self):
		resp = self.client.post(reverse('update_profile'), {'first_name': 'new','institution':"Testing",'country':"GB"})
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp['Location'], "http://testing/user/profile/")

	def test_register(self):
		resp = self.client.post(reverse('register'), {'first_name': 'new','last_name':'last','username':'user1','email':'fake@faked.com','password1': 'password1','password2':"password1"})
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp['Location'], "http://testing/login/")

	def test_reset_password(self):
		resp = self.client.post(reverse('reset_password'), {'password_1': 'password1','password_2':"password1"})
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp['Location'], "http://testing/login/")

	def test_register_login(self):
		resp = self.client.post(reverse('register'), {'first_name': 'new','last_name':'last','username':'user1','email':'fake@faked.com','password1': 'password1','password2':"password1"})
		user = User.objects.get(username="user1")
		roles = models.Role.objects.filter(name__icontains="Editor")
		for role in roles:
			user.profile.roles.add(role)
		user.active=True
		user.save()
		user.profile.save()
		resp = self.client.post(reverse('login'),{'username': 'user1','password':"password1"})
		self.assertEqual(resp['Location'], "http://testing/dashboard/")
		


		#### Problematic ###

	'''def test_book_model(self):
		"""
		test book model
		"""
		self.author = models.Author(
			first_name = "rua_first_name",
			last_name = "rua_last_name",
			salutation = "Mr",
			institution = "Testing",
			department = "test",
			country = "GB",
			author_email = "fake@fakeaddress.com"
			)
		self.author.save()
		self.keyword=models.Keyword(name="test")
		self.keyword.save()
		self.subject=models.Subject(name="test")
		self.subject.save()
		user=self.user
		self.book= models.Book(
				prefix = "Project",
				title = "Test Book",
				author = [self.author,],
				press_editors = [self.user,],
				description = "description",
				keywords = [self.keyword,],
				subject = [self.subject,],
				license = models.License.objects.get(code="cc-4-by-nd"),
				pages = "50",
				slug = "test_book",
				cover_letter = "cover letter text",
				reviewer_suggestions = "suggestions",
				competing_interests = "interests",
				book_type = 'monograph',
				review_type = 'open-with',
				languages = models.Language.objects.get(code="eng"),
				owner = user
			)
		self.book.save()
		#check that it exists in the database
		
		self.assertEqual(len(models.Book.objects.all())==1, True)	'''
		
