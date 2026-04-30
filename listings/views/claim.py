from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from listings.models import Listing, ListingClaim
from listings.forms import ClaimForm


@login_required
def claim_business(request, slug):
    listing = get_object_or_404(Listing, slug=slug)

    existing_claim = ListingClaim.objects.filter(
        listing=listing,
        user=request.user
    ).first()

    if existing_claim:
        messages.info(request, 'You have already submitted a claim for this business.')
        return redirect('listing_detail', slug=slug)

    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim = ListingClaim.objects.create(
                listing=listing,
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                role=form.cleaned_data['role'],
                verification_method=form.cleaned_data['verification_method'],
                business_phone=form.cleaned_data.get('business_phone', ''),
                note=form.cleaned_data.get('note', ''),
                status='pending'
            )

            send_mail(
                subject=f'[find.ng] New claim: {listing.name}',
                message=(
                    f'A new business claim has been submitted on find.ng.\n\n'
                    f'Business:   {listing.name}\n'
                    f'Category:   {listing.get_category_display()}\n'
                    f'Address:    {listing.address}\n\n'
                    f'Claimed by: {claim.full_name}\n'
                    f'Phone:      {claim.phone}\n'
                    f'Role:       {claim.get_role_display()}\n'
                    f'Verification: {claim.get_verification_method_display()}\n'
                    f'Note:       {claim.note or "None"}\n\n'
                    f'Submitted:  {claim.claimed_at.strftime("%d %b %Y, %I:%M %p")}\n\n'
                    f'Review and approve/reject this claim in Django admin:\n'
                    f'https://your-render-domain.onrender.com/admin/listings/listingclaim/{claim.id}/change/'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )

            messages.success(request, 'Your claim has been submitted. We will contact you within 48 hours.')
            return redirect('listing_detail', slug=slug)
    else:
        form = ClaimForm(initial={'role': 'owner', 'verification_method': 'business_phone'})

    context = {
        'listing': listing,
        'form': form,
        'whatsapp_number': '2348030000000',
    }
    return render(request, 'listings/claim.html', context)