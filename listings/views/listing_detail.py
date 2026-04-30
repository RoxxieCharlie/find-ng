from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Q
from django.utils import timezone
from listings.models import Listing, Review

_DAY_ORDER = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
_DAY_NOW   = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}


def listing_detail(request, slug):
    listing = get_object_or_404(
        Listing.objects
        .prefetch_related(
            'photos', 'hours', 'accepted_payments',
            'menu_items', 'room_type', 'amenities',
            'activities', 'products', 'facilities',
        )
        .annotate(
            review_count=Count('reviews', filter=Q(reviews__is_flagged=False)),
            avg_rating=Avg('reviews__star_rating', filter=Q(reviews__is_flagged=False)),
        ),
        slug=slug, is_active=True,
    )

    today_key    = _DAY_NOW[timezone.localtime().weekday()]
    hours_sorted = sorted(listing.hours.all(), key=lambda h: _DAY_ORDER.get(h.day, 7))
    cover_photo  = (
        listing.photos.filter(photo_type='exterior').first()
        or listing.photos.first()
    )
    reviews = (
        listing.reviews
        .filter(is_flagged=False)
        .select_related('user')
        .order_by('-created_at')[:10]
    )

    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            listing=listing,
            user=request.user,
        ).first()

    return render(request, 'listings/listing_detail.html', {
        'listing':       listing,
        'user_claim':    listing.get_user_claim(request.user),
        'cover_photo':   cover_photo,
        'photos':        listing.photos.all(),
        'hours_sorted':  hours_sorted,
        'today_key':     today_key,
        'reviews':       reviews,
        'user_review':   user_review,
        'is_food':       listing.category in ('restaurant', 'bukka', 'bar'),
        'is_hotel':      listing.category == 'hotel',
        'is_shop':       listing.category == 'shop',
        'is_recreation': listing.category == 'recreation',
    })