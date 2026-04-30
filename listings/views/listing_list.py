from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from listings.models import Listing

_CATEGORY_DISPLAY = {
    'hotel':      'Hotels',
    'restaurant': 'Restaurants',
    'bukka':      'Bukkas',
    'bar':        'Bars',
    'shop':       'Shops',
    'recreation': 'Recreation',
}

_DAY_ORDER = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
_DAY_NOW   = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}


def _page_range(page_obj, window=2):
    n, total = page_obj.number, page_obj.paginator.num_pages
    pages = set([1, 2, total - 1, total])
    pages.update(range(max(1, n - window), min(total, n + window) + 1))
    result, prev = [], None
    for p in sorted(p for p in pages if 1 <= p <= total):
        if prev and p - prev > 1:
            result.append(None)
        result.append(p)
        prev = p
    return result

def listing_list(request):
    category = request.GET.get('category', '')
    area     = request.GET.get('area', '')
    status   = request.GET.get('status', '')
    sort     = request.GET.get('sort', 'top')
    q        = request.GET.get('q', '').strip()

    qs = (
        Listing.objects
        .filter(is_active=True)
        .annotate(
            review_count=Count('reviews', filter=Q(reviews__is_flagged=False)),
            avg_rating=Avg('reviews__star_rating', filter=Q(reviews__is_flagged=False)),
        )
        .prefetch_related('photos', 'hours')
    )

    if category:
        qs = qs.filter(category=category)

    _area_map = {
        'town-centre':   'town centre',
        'finima':        'finima',
        'abalamabie':    'abalamabie',
        'pepple-street': 'pepple street',
    }
    if area in _area_map:
        qs = qs.filter(address__icontains=_area_map[area])

    if status == 'verified':
        qs = qs.filter(is_verified=True)

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(address__icontains=q) | Q(description__icontains=q)
        )

    qs = qs.order_by('-is_verified', '-avg_rating', '-created_at') if sort == 'top' \
        else qs.order_by('-is_verified', '-created_at')

    if status == 'open':
        items       = [l for l in list(qs) if l.is_open_now()]
        total_count = len(items)
        paginator   = Paginator(items, 8)
    else:
        total_count = qs.count()
        paginator   = Paginator(qs, 8)

    page_obj = paginator.get_page(request.GET.get('page', 1))

    base_qs          = Listing.objects.filter(is_active=True)
    category_options = [
        (k, _CATEGORY_DISPLAY.get(k, v.strip()), base_qs.filter(category=k).count())
        for k, v in Listing.CATEGORY_CHOICES
    ]
    area_options = [
        ('town-centre',   'Town centre',   base_qs.filter(address__icontains='town centre').count()),
        ('finima',        'Finima',        base_qs.filter(address__icontains='finima').count()),
        ('abalamabie',    'Abalamabie',    base_qs.filter(address__icontains='abalamabie').count()),
        ('pepple-street', 'Pepple street', base_qs.filter(address__icontains='pepple street').count()),
    ]

    qp = request.GET.copy()
    qp.pop('page', None)
    query_string = qp.urlencode()

    qp_no_cat = request.GET.copy()
    qp_no_cat.pop('category', None)
    qp_no_cat.pop('page', None)

    return render(request, 'listings/listing_list.html', {
        'page_obj':             page_obj,
        'total_count':          total_count,
        'total_category_count': base_qs.count(),
        'category':             category,
        'area':                 area,
        'status':               status,
        'sort':                 sort,
        'q':                    q,
        'category_options':     category_options,
        'area_options':         area_options,
        'query_string':         query_string,
        'base_qs_no_category':  qp_no_cat.urlencode(),
        'page_range_display':   _page_range(page_obj),
    })
