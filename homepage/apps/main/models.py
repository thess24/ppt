from django.db import models
from django.forms import ModelForm, Textarea
from django import forms
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from tinymce import models as tinymce_models
from tinymce.widgets import TinyMCE
import os
from settings.common import MAX_FILE_SIZE, MAX_IMG_SIZE, ALLOWED_FILE_TYPES, ALLOWED_IMG_TYPES
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from crispy_forms.bootstrap import PrependedText, StrictButton


class Product(models.Model):

	CATEGORIES = (
	('Maps','Maps'),
	('Business','Business'),
	('Finance','Finance'),
	('Marketing','Marketing'),
	('Health/Fitness','Health/Fitness'),
	('Real Estate','Real Estate'),
	('Science','Science'),
	('Maps','Sports'),
	('Technology','Technology'),
	('Education','Education'),
	('Design','Design'),
	('Nature','Nature'),
	)
 


	name = models.CharField(max_length=140)
	added_date = models.DateTimeField(auto_now_add=True)
	description = tinymce_models.HTMLField()
	purchases = models.IntegerField(default=0) 
	product_file = models.FileField(upload_to='files')
	price = models.DecimalField(max_digits=6, decimal_places=2)
	sale_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	image = models.ImageField(upload_to='products')
	category = models.CharField(max_length=40, choices=CATEGORIES)
	pages = models.IntegerField(blank=True,null=True)
	user_created = models.ForeignKey(User)
	active = models.BooleanField(default=False)
	popular = models.BooleanField(default=False)
	featured = models.BooleanField(default=False)
	new = models.BooleanField(default=True)

	tags = TaggableManager()

	def current_price(self):
		if self.sale_price: return self.sale_price
		else: return self.price

	def __unicode__(self):
		return self.name

class ProductImage(models.Model):
	product = models.ForeignKey(Product)
	text = models.CharField(max_length=140,blank=True, null=True)
	added_date = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(upload_to='products')
  
	def __unicode__(self):
		return self.product.name

class Purchase(models.Model):
	user = models.ForeignKey(User, blank=True, null=True)
	product = models.ForeignKey(Product)
	sale_date = models.DateTimeField(auto_now_add=True)
	downloads = models.IntegerField()
	email = models.EmailField()
	uuid = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=6, decimal_places=2)

	def active_to_download(self):
		if self.downloads <=0: return False
		else: return True

	def __unicode__(self):
		return self.product.name

class UserCard(models.Model):
	user = models.OneToOneField(User)
	usertoken = models.CharField(max_length=150)

	def __unicode__(self):
		return self.user.email

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	access_token = models.CharField(max_length=200, null=True, blank=True)
	refresh_token = models.CharField(max_length=200, null=True, blank=True)
	stripe_publishable_key = models.CharField(max_length=200, null=True, blank=True)

	def __unicode__(self):
		return self.user.email



##########    FORMS   ############



class ProductForm(ModelForm):
	description = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 15}))

	class Meta:
		model = Product
		exclude = ['purchases', 'user_created', 'active', 'new', 'popular', 'featured']

	def clean(self):
		cleaned_data = super(ProductForm, self).clean()
		image = cleaned_data.get('image',False)
		product_file = cleaned_data.get('product_file',False)
		product_name = cleaned_data.get('name',False)

		pname = Product.objects.filter(name=product_name)
		if pname:
			raise ValidationError("That name already exists")

		if image:
			if image._size > MAX_IMG_SIZE:
				raise ValidationError("Image too large - must be less than 300kb")

			imgtype = image.name.split(".")[-1]
			if imgtype not in ALLOWED_IMG_TYPES:
				raise ValidationError("Must by a jpg, jpeg, gif, or png")

		if product_file:
			filetype = product_file.name.split(".")[-1]
			if filetype not in ALLOWED_FILE_TYPES:
				raise ValidationError("Must by a ppt, potx, or pptx")

			if product_file._size > MAX_FILE_SIZE:
				raise ValidationError("File too large - must be less than 4mb")

		return cleaned_data

	def __init__(self, *args, **kwargs):
		super(ProductForm, self).__init__(*args, **kwargs)
		self.helper= FormHelper()
		self.helper.form_class = 'form-horizontal'
		self.helper.label_class = 'col-lg-3'
		self.helper.field_class = 'col-lg-9'
		self.helper.layout = Layout(
				'name' ,
				'description' ,
				PrependedText('price', '$'),
				'product_file' ,
				'image' ,
				'category' ,
				'pages' ,
				'tags' ,
				StrictButton('Continue >', name='addproduct', type='submit',css_class='btn-primary btn-lg'),
		)



class ProductEditForm(ProductForm):
	class Meta:
		model = Product
		exclude = ['purchases', 'user_created', 'active', 'new', 'popular', 'featured','name','pages','product_file']