from django.shortcuts import render, get_object_or_404
from apps.main.models import Product, Purchase, ProductImage, ProductForm,ProductEditForm, UserProfile
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
from django.db.models import Sum
import requests
from django.contrib import messages
from django.conf import settings
import boto

def index(request):
	products = Product.objects.filter(active=True)

	if request.method == "GET":
		if request.GET.get('type'):
			sorttype = request.GET.get('type')
			if not sorttype in ['popular', 'featured', 'recent']: raise Http404

			if sorttype=='popular': 
				products.order_by('purchases','-added_date')
			if sorttype=='featured': 
				products.order_by('featured','-added_date')
			if sorttype=='recent': 
				products.order_by('-added_date')

	context= {'products':products}
	return render(request, 'main/index.html', context)

def productpage(request, productid):
	product = Product.objects.get(id=productid)
	productimages = ProductImage.objects.filter(product=product)
	similarproducts = product.tags.similar_objects()
	stripeprice = product.price *100

	context= {'product':product, 'productimages':productimages, 'stripeprice':stripeprice, 'similarproducts':similarproducts}
	return render(request, 'main/productpage.html', context)

@login_required
def editproduct(request, productid):
	try: product = Product.objects.get(id=productid)
	except: return render(request, 'main/editproduct.html', {'errormessage':'Product Does Not Exist!'})

	if not product.user_created == request.user: 
		return render(request, 'main/editproduct.html', {'errormessage':"You can't edit a product you didn't upload"})

	if product.active: 
		return render(request, 'main/editproduct.html', {'errormessage':"This product is live and cannot be changed currently.  Please contact us to make changes."})


	form = ProductEditForm(instance=product)

	if request.method=='POST':
		if 'addproduct' in request.POST:
			form = ProductEditForm(request.POST, request.FILES,instance=product)
			if form.is_valid():
				instance = form.save(commit=False)
				# instance.user_created=request.user
				instance.save()
				form.save_m2m()

				return HttpResponseRedirect(reverse('apps.main.views.index', args=()))

	context= {'product':product, 'form':form}
	return render(request, 'main/editproduct.html', context)

@login_required
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
# Production
if settings.PRODUCTION:
	filepath = product.product_file.url

	conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
	bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
	s3_file_path = bucket.get_key(filepath)


	response_headers = {
		'response-content-type': 'application/force-download',
		'response-content-disposition':'attachment;filename="%s"'%product.name
	}

	url = s3_file_path.generate_url(600, 'GET',
		bucket=settings.AWS_STORAGE_BUCKET_NAME,
		key=filepath,
		response_headers=response_headers,
		force_http=True)

	return http.HttpResponseRedirect(url)


	# the_file = os.path.normpath(settings.STORAGE_ROOT + product.product_file.url)
	# the_file = product.product_file.url
	# # filename = os.path.basename(the_file)
	# filename = os.path.basename(product.product_file.url)
	# response = HttpResponse(FileWrapper(open(the_file)),
	# 					content_type=mimetypes.guess_type(the_file)[0])
	# response['Content-Length'] = os.path.getsize(the_file)    
	# response['Content-Disposition'] = "attachment; filename=%s" % filename
	# return response
else:
# Development    
	the_file = product.product_file.path                            
	filename = os.path.basename(the_file)
	response = HttpResponse(FileWrapper(open(the_file)),
						content_type=mimetypes.guess_type(the_file)[0])
	response['Content-Length'] = os.path.getsize(the_file)    
	response['Content-Disposition'] = "attachment; filename=%s" % filename
	return response


@login_required
def upload(request):
	profile , c = UserProfile.objects.get_or_create(user=request.user)
	if not profile.access_token:
		return HttpResponseRedirect(reverse('apps.main.views.acceptpayments', args=()))

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

@login_required
def salescenter(request):
	sales = Purchase.objects.filter(product__user_created=request.user).order_by('sale_date')
	products = Product.objects.filter(user_created=request.user).annotate(Sum('purchase__price'))
	monthly = Product.objects.filter(user_created=request.user,added_date__gte=datetime.datetime.now()- datetime.timedelta(days=30)).annotate(Sum('purchase__price'))
	weekly = Product.objects.filter(user_created=request.user,added_date__gte=datetime.datetime.now()- datetime.timedelta(days=7)).annotate(Sum('purchase__price'))
	# print monthly[0].purchase__price__sum  #need to do nested loops in template

	# tempmorrislist = []
	# for keydate, group in groupby(sales,lambda x: x.sale_date.date()):
	# 	thelist = [(x.product.name,x.price) for x in group]

	# 	testDict = defaultdict(int)
	# 	for key, val in thelist:
	# 		testDict[key] += val

	# 	tempmorrislist.append( [keydate, testDict] )

	# morrislist=[]
	# for i in tempmorrislist:
	# 	keylist = []
	# 	string = "{ date: '"+ str(i[0])+"'"
	# 	for j,k in i[1].items():
	# 		string += ','+j+':'+str(k)
	# 	string +='},'
	# 	morrislist.append(string)



	context= {'sales':sales, 'products':products, 'monthly':monthly, 'weekly':weekly}
	return render(request, 'main/salescenter.html', context)

def category(request, category):
	products = Product.objects.filter(category__iexact=category.lower(),active=True)

	if not products: raise Http404  # 404 if category not accepted, if it is, say something

	context= {'products':products, 'category':category}
	return render(request, 'main/category.html', context)

def search(request):
	if request.method=='GET':
		if request.GET.get('searchstring'):
			searchstring = request.GET.get('searchstring')

	products = Product.objects.filter(tags__name__in=[searchstring],active=True)

	header = 'Search: '+searchstring

	context= {'products':products, 'category':header}
	return render(request, 'main/category.html', context)

def charge(request):
	# Set your secret key: remember to change this to your live secret key in production
	# See your keys here https://manage.stripe.com/account
	# stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"  #only for universal, this is a marketplace so every vendor has their own

	token = request.POST.get('stripeToken')
	email = request.POST.get('stripeEmail')
	try:productid = request.POST['productid']
	except: raise Http404  #put better error here

	product = Product.objects.get(id=productid)
	product_price = product.price
	product_amt = product_price*100
	mycut = product_amt*3/10

	a,b = UserProfile.objects.get_or_create(user=request.user)
	publishkey = product.user_created.userprofile.stripe_publishable_key
	accesstoken = product.user_created.userprofile.access_token


	try:
		charge = stripe.Charge.create(
			amount=product_amt, 
			currency="usd",
			card=token,
			description=email,
			application_fee= mycut,
			api_key = accesstoken,
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


	product.purchases+=1
	product.save()

	# send email
	plaintext = get_template('downloademail.txt')
	htmly = get_template('downloademail.html')
	d = Context({ 'purchase': purchase })
	subject, from_email, to = 'Download Link', 'from@example.com', 'thess624@gmail.com'
	text_content = plaintext.render(d)
	html_content = htmly.render(d)
	msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
	msg.attach_alternative(html_content, "text/html")
	msg.send()


	context= {'purchase':purchase}
	return render(request, 'main/success.html', context)

@login_required
def multiupload(request):
	response = {'files': []}
	try: 
		productid = request.POST['productid']
		p = Product.objects.get(id=productid)
	except: raise Http404  

	try: 
		productid = request.POST['productid']
		p = Product.objects.get(id=productid)
	except: raise Http404

	if not p.user_created == request.user: raise Http404  #this is fine

	images = ProductImage.objects.filter(product=p).count()
	if int(images)>15: print 'hey 404'  #send response of too many images

	# Loop through our files in the files list uploaded
	for image in request.FILES.getlist('files[]'):  #this only has one file as of now
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

@login_required
def uploadimages(request, productid):
	try: product = Product.objects.get(id=productid)
	except: raise Http404

	if not product.user_created == request.user: raise Http404

	productimages = ProductImage.objects.filter(product=product)

	context= {'product':product, 'productimages':productimages}
	return render(request, 'main/uploadimages.html', context)

@login_required
def acceptpayments(request):
	return render(request, 'main/acceptpayments.html')

@login_required
def striperesponse(request):
	code = request.GET.get('code')
	profile,c = UserProfile.objects.get_or_create(user=request.user)

	r = requests.post('https://connect.stripe.com/oauth/token', params={
		'client_secret': 'sk_test_ChZBYMHbZLagr8DQdsqxcq9y',
		'code': code,
		'grant_type': 'authorization_code'
	}).json()

	try:
		profile.access_token = r['access_token']
		profile.refresh_token = r['refresh_token']
		profile.stripe_publishable_key = r['stripe_publishable_key']
		profile.save()

		# messages.success(request, "Your account was successfully connected to Stripe.")
	except KeyError:
		raise Http404
		# messages.error(request, "Unable to connect your account to Stripe.")

	print r
	# context= {'product':product, 'productimages':productimages}
	return render(request, 'main/striperesponse.html')

@csrf_exempt
def deleteimage(request, imageid):
	try: image = ProductImage.objects.get(id=imageid)
	except: raise Http404

	image.delete()

	return HttpResponse('')

def howbuyingworks(request):
	return render(request, 'main/howbuyingworks.html')	

def howsellingworks(request):
	return render(request, 'main/howsellingworks.html')	



def tos(request):
	return render(request, 'main/tos.html')	

def privacypolicy(request):
	return render(request, 'main/privacypolicy.html')

def faq(request):
	return render(request, 'main/faq.html')	