from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from listings.forms import LoginForm, RegisterForm
from listings.models import User
from listings.models import User, ListingClaim, Review  # add ListingClaim, Review to your existing import


@login_required
def account_view(request):
    user = request.user

    user_claims = (
        ListingClaim.objects
        .filter(user=user)
        .select_related('listing')
        .order_by('-claimed_at')
    )

    user_reviews = (
        Review.objects
        .filter(user=user)
        .select_related('listing')
        .order_by('-created_at')
    )

    # unified activity feed, newest first
    activity = []
    for r in user_reviews:
        activity.append({
            'type':       'review',
            'listing':    r.listing,
            'rating':     r.star_rating,
            'created_at': r.created_at,
        })
    for c in user_claims:
        activity.append({
            'type':       'claim',
            'listing':    c.listing,
            'created_at': c.claimed_at,
        })

    activity.sort(key=lambda x: x['created_at'], reverse=True)

    context = {
        'user_claims':          user_claims,
        'user_reviews':         user_reviews,
        'latest_claim':         user_claims.first(),
        'reviews_count':        user_reviews.count(),
        'claims_count':         user_claims.count(),
        'pending_claims_count': user_claims.filter(status='pending').count(),
        'recent_activity':      activity[:5],
    }

    return render(request, 'listings/account.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            user = authenticate(request, username=phone, password=password)
            if user:
                login(request, user)
                return redirect(next_url or 'home')
            else:
                form.add_error(None, 'Invalid phone number or password.')
    else:
        form = LoginForm()

    return render(request, 'listings/login.html', {
        'form': form,
        'next': next_url,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next', '')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                phone=form.cleaned_data['phone'],
                full_name=form.cleaned_data['full_name'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            return redirect(next_url or 'home')
    else:
        form = RegisterForm()

    return render(request, 'listings/register.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    logout(request)
    return redirect('home')