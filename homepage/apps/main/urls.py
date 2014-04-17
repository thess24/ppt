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
	url(r'^sellerhistory/$', views.sellerhistory, name='sellerhistory'),
	url(r'^c/(?P<category>.+)/$', views.category, name='category'),
	url(r'^multiupload/$', views.multiupload, name='multiupload'),


	(r'^media/(?P<path>.*)$', 'django.views.static.serve',
		{'document_root': MEDIA_ROOT}),
)




# option to download now or create account (if not logged in) -- modal 
# fix price and sale price
# make page for seller history


########## OPTIONAL ############
# video embed optional
# search
# view past viewed



########### IMPORTANT ###########

# flow process for uploads -- first info, they once submitted, do images
# error handling for imagesupload
# form errors - file restriction, size, type for multiupload


#### stripe
# error handling
# make sure only one card on file at a time - display what the card is
# make it a marketplace and take percentage, not one sided