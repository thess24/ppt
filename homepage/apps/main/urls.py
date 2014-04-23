from django.conf.urls import patterns, url
from apps.main import views
from django.conf import settings
from django.conf.urls.static import static
from settings.common import MEDIA_ROOT

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^product/(?P<productid>.+)/edit/$', views.editproduct, name='editproduct'),
	url(r'^product/(?P<productid>.+)/$', views.productpage, name='productpage'),
	url(r'^download/(?P<purchaseuuid>.+)/$', views.downloadpage, name='downloadpage'),
	url(r'^purchases/$', views.purchases, name='purchases'),
	url(r'^charge/$', views.charge, name='charge'),
	url(r'^upload/$', views.upload, name='upload'),
	url(r'^uploadimages/(?P<productid>.+)/$', views.uploadimages, name='uploadimages'),
	url(r'^image/delete/(?P<imageid>.+)/$', views.deleteimage, name='deleteimage'),
	url(r'^salescenter/$', views.salescenter, name='salescenter'),
	url(r'^c/(?P<category>.+)/$', views.category, name='category'),
	url(r'^search/$', views.search, name='search'),
	url(r'^multiupload/$', views.multiupload, name='multiupload'),
	url(r'^acceptpayments/$', views.acceptpayments, name='acceptpayments'),
	url(r'^acceptpayments/striperesponse/$', views.striperesponse, name='striperesponse'),

	url(r'^howbuyingworks/$', views.howbuyingworks, name='howbuyingworks'),
	url(r'^howsellingworks/$', views.howsellingworks, name='howsellingworks'),
	url(r'^tos/$', views.tos, name='tos'),
	url(r'^privacypolicy/$', views.privacypolicy, name='privacypolicy'),
	url(r'^faq/$', views.faq, name='faq'),


	(r'^media/(?P<path>.*)$', 'django.views.static.serve',
		{'document_root': MEDIA_ROOT}),
)

##########  OPTIONAL #######
# option to download now or create account (if not logged in) -- modal 
# fix price and sale price
# ability to save presentations
# pagination



########### IMPORTANT ##########
# front end file size checking
# salescenter fix -- weekly sales, monthly sales (hide graph for now)
# get stripe connect to work
# get django messages working
# do faq and tos and privacy policy




#### stripe
# error handling
# make sure only one card on file at a time - display what the card is
# make it a marketplace and take percentage, not one sided







# maps
# business
# health/fitness
# food
# real estate
# science
# sports
# technology
# education
# design
# nature


# Monday
# --stripe connect

# Tuesday
# --testing and socialmedia

# Wednesday
# --on heroku