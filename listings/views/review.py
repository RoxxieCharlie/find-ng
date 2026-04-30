# listings/views/review.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from listings.models import Listing, Review


@login_required
def review_create(request, slug):
    listing = get_object_or_404(Listing, slug=slug, is_active=True)

    if Review.objects.filter(listing=listing, user=request.user).exists():
        return redirect('listing_detail', slug=slug)

    if request.method == 'POST':
        star_rating = int(request.POST.get('star_rating', 0))
        comment     = request.POST.get('comment', '').strip()

        if 1 <= star_rating <= 5:
            Review.objects.create(
                listing     = listing,
                user        = request.user,
                star_rating = star_rating,
                comment     = comment,
            )

    return redirect('listing_detail', slug=slug)


@login_required
def review_edit(request, slug):
    listing = get_object_or_404(Listing, slug=slug, is_active=True)
    review  = get_object_or_404(Review, listing=listing, user=request.user)

    if request.method == 'POST':
        star_rating = int(request.POST.get('star_rating', 0))
        comment     = request.POST.get('comment', '').strip()

        if 1 <= star_rating <= 5:
            review.star_rating = star_rating
            review.comment     = comment
            review.save()

    return redirect('listing_detail', slug=slug)