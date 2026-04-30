from django.urls import path
from listings.views import home, listing_list, listing_detail
from listings.views.claim import claim_business
from listings.views.account import login_view, register_view, logout_view, account_view
from listings.views.review import review_create, review_edit
from listings.views.search import search


urlpatterns = [
    path('', home, name='home'),
    path('search/', search, name='search'),
    path('listings/', listing_list, name='listing_list'),
    path('listings/<slug:slug>/', listing_detail, name='listing_detail'),
    path('listings/<slug:slug>/review/', review_create, name='review_create'),
    path('listings/<slug:slug>/review/edit/', review_edit, name='review_edit'),
    path('business/<slug:slug>/claim/', claim_business, name='claim'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('account/', account_view, name='account'),
]