from django.shortcuts import render, get_object_or_404
from apps.main.models import Product, Purchase, ProductImage, UserCard, ProductForm
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import stripe
from django.core.servers.basehttp import FileWrapper
from settings.common import MEDIA_ROOT, MAX_IMG_SIZE
import os, datetime, mimetypes, json, uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.views.decorators.csrf import csrf_exempt
from itertools import groupby
from collections import defaultdict


def index(request):
	products = Product.objects.all()
	context= {'products':products}
	return render(request, 'main/index.html', context)

def productpage(request, productid):
	product = Product.objects.get(id=productid)
	productimages = ProductImage.objects.filter(product=product)
	similarproducts = product.tags.similar_objects()
	stripeprice = product.price *100

	try:
		customer = UserCard.objects.get(user=request.user)
		customer_id = customer.usertoken
	except:
		customer_id = None	

	context= {'product':product, 'productimages':productimages, 'stripeprice':stripeprice, 'similarproducts':similarproducts}
	return render(request, 'main/productpage.html', context)

def editproduct(request, productid):
	try: product = Product.objects.get(id=productid)
	except: raise Http404

	if not product.user_created == request.user: raise Http404

	form = ProductForm(instance=product)

	if request.method=='POST':
		if 'addproduct' in request.POST:
			form = ProductForm(request.POST, request.FILES)
			if form.is_valid():
				instance = form.save(commit=False)
				instance.save()
				form.save_m2m()

				return HttpResponseRedirect(reverse('apps.main.views.index', args=()))

	context= {'product':product, 'form':form}
	return render(request, 'main/editproduct.html', context)

def purchases(request):
	purchases = Purchase.objects.filter(user=request.user)

	context= {'purchases':purchases}
	return render(request, 'main/purchases.html', context)

def downloadpage(request, purchaseuuid):
	purchase = Purchase.objects.get(uuid=purchaseuuid)
	product = Product.objects.get(id=purchase.product.id)

	if purchase.downloads <=0:
		raise Http404
		# should display error to say dl limit reached

	purchase.downloads -=1
	purchase.save()


	"""                                                                         
	Send a file through Django without loading the whole file into              
	memory at once. The FileWrapper will turn the file object into an           
	iterator for chunks of 8KB.                                                 
	"""
	the_file = product.product_file.path # Select your file here.                                
	filename = os.path.basename(the_file)
	response = HttpResponse(FileWrapper(open(the_file)),
						content_type=mimetypes.guess_type(the_file)[0])
	response['Content-Length'] = os.path.getsize(the_file)    
	response['Content-Disposition'] = "attachment; filename=%s" % filename
	return response


@login_required
def upload(request):
	form = ProductForm()

	if request.method=='POST':
		if 'addproduct' in request.POST:
			form = ProductForm(request.POST, request.FILES)
			if form.is_valid():
				instance = form.save(commit=False)
				instance.user_created = request.user
				instance.save()
				form.save_m2m()

				return HttpResponseRedirect(reverse('apps.main.views.uploadimages', args=(instance.id,)))

	context= {'form':form}
	return render(request, 'main/upload.html', context)

def salescenter(request):
	sales = Purchase.objects.filter(product__user_created=request.user).order_by('sale_date')
	products = Product.objects.filter(user_created=request.user)

	tempmorrislist = []
	for keydate, group in groupby(sales,lambda x: x.sale_date.date()):
		# import pdb;pdb.set_trace()
		# listOfThings = " and ".join(["%s" % thing.product.name for thing in group])
		# print key
		thelist = [(x.product.name,x.price) for x in group]

		testDict = defaultdict(int)
		for key, val in thelist:
			testDict[key] += val

		tempmorrislist.append( [keydate, testDict] )

	morrislist=[]
	for i in tempmorrislist:
		keylist = []
		string = "{ date: '"+ str(i[0])+"'"
		for j,k in i[1].items():
			string += ','+j+':'+str(k)
		string +='},'
		morrislist.append(string)



	context= {'sales':sales, 'products':products, 'morrislist':morrislist}
	return render(request, 'main/salescenter.html', context)

def category(request, category):
	products = Product.objects.filter(category__iexact=category.lower())
	context= {'products':products}
	return render(request, 'main/index.html', context)

def charge(request):
	# Set your secret key: remember to change this to your live secret key in production
	# See your keys here https://manage.stripe.com/account
	stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"

	token = request.POST.get('stripeToken')
	email = request.POST.get('stripeEmail')
	try:productid = request.POST['productid']
	except: raise Http404  #put better error here

	product = Product.objects.get(id=productid)
	product_price = product.price
	product_amt = product_price*100

	if request.user.is_authenticated():
		email = request.user.email
		try:
			customer = UserCard.objects.get(user=request.user)
			customer_id = customer.usertoken
		except:
			customer_id = None	

		if not customer_id:
			customer = stripe.Customer.create(
				card=token,
				description=email
			)
			c = UserCard(user=request.user, usertoken=customer.id)
			c.save()
			customer_id = customer.id

		try:
			stripe.Charge.create(
			amount=product_amt, 
			currency="usd",
			customer=customer_id
			)
		except stripe.CardError, e:
		  # The card has been declined
		  # render error template
			pass


	else:  # not registered user, just entered card info
		try:
			charge = stripe.Charge.create(
				amount=product_amt, 
				currency="usd",
				card=token,
				description=email
			)
		except stripe.CardError, e:
		  # The card has been declined
		  # render error template
			pass

	# create purchase record
	if request.user.is_authenticated():
		purchase = Purchase(user=request.user, price=product_price, product=product, email=email, downloads=5, uuid=str(uuid.uuid4()))
	else:
		purchase = Purchase(product=product, price=product_price ,email=email, downloads=5, uuid=str(uuid.uuid4()))
	purchase.save()


	# send email
	plaintext = get_template('downloademail.txt')
	htmly     = get_template('downloademail.html')
	d = Context({ 'purchase': purchase })
	subject, from_email, to = 'Download Link', 'from@example.com', 'thess624@gmail.com'
	text_content = plaintext.render(d)
	html_content = htmly.render(d)
	msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
	msg.attach_alternative(html_content, "text/html")
	msg.send()


	context= {'purchase':purchase}
	return render(request, 'main/success.html', context)

def multiupload(request):
	response = {'files': []}
	try: 
		productid = request.POST['productid']
		print productid
		p = Product.objects.get(id=productid)
	except: raise Http404

	# Loop through our files in the files list uploaded
	for image in request.FILES.getlist('files[]'):
		if image._size > MAX_IMG_SIZE:
			continue  #probably should send error here
		
		new_image = ProductImage(product=p, image=image)
		# Save the image using the model's ImageField settings
		# filename, ext = os.path.splitext(image.name)
		new_image.save()
		# Save output for return as JSON
		response['files'].append({
			'name': '%s' % image.name,
			'size': '%d' % image.size,
			# 'url': '%s' % new_image.image.url,
			# 'thumbnailUrl': '%s' % new_image.image.url,
			'deleteUrl': '/image/delete/%s/' % new_image.id,
			"deleteType": 'DELETE'
		})

	return HttpResponse(json.dumps(response), content_type='application/json')

def uploadimages(request, productid):
	try: product = Product.objects.get(id=productid)
	except: raise Http404

	if not product.user_created == request.user: raise Http404

	productimages = ProductImage.objects.filter(product=product)

	context= {'product':product, 'productimages':productimages}
	return render(request, 'main/uploadimages.html', context)

@csrf_exempt
def deleteimage(request, imageid):
	try: image = ProductImage.objects.get(id=imageid)
	except: raise Http404

	image.delete()

	return HttpResponse('')