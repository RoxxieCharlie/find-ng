from django.shortcuts import render
from django.db.models import Count, Avg, Q
from listings.models import Listing


def home(request):
    verified_listings = (
        Listing.objects
        .filter(is_verified=True, is_active=True)
        .annotate(
            review_count=Count('reviews', filter=Q(reviews__is_flagged=False)),
            avg_rating=Avg('reviews__star_rating', filter=Q(reviews__is_flagged=False)),
        )
        .prefetch_related('photos')
        [:6]
    )

    nearby_listings = (
        Listing.objects
        .filter(is_active=True)
        .order_by('-is_verified', '-created_at')
        [:10]
    )

    return render(request, 'listings/home.html', {
        'verified_listings': verified_listings,
        'nearby_listings':   nearby_listings,
        'location':          'Bonny Island, Rivers State',
        'nearby_area':       'Bonny town',
    })
