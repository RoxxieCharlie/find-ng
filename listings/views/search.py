# listings/views/search.py

from django.shortcuts import render
from django.db.models import Count, Avg, Q
from listings.models import Listing


def search(request):
    query    = request.GET.get('q', '').strip()
    results  = []
    searched = False

    if query:
        searched = True
        results = (
            Listing.objects
            .filter(is_active=True)
            .filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(landmark__icontains=query) |
                Q(category__icontains=query)
            )
            .annotate(
                review_count=Count('reviews', filter=Q(reviews__is_flagged=False)),
                avg_rating=Avg('reviews__star_rating', filter=Q(reviews__is_flagged=False)),
            )
            .prefetch_related('photos')
            .order_by('-is_verified', '-created_at')
        )

    return render(request, 'listings/search.html', {
        'query':    query,
        'results':  results,
        'searched': searched,
        'count':    results.count() if searched else 0,
    })