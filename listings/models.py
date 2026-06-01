from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone


# ── User ──────────────────────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, phone, full_name, password=None):
        if not phone:
            raise ValueError('Phone number is required')
        user = self.model(phone=phone, full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, full_name, password):
        user = self.create_user(phone, full_name, password)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username        = None
    full_name       = models.CharField(max_length=50)
    phone           = models.CharField(max_length=20, unique=True)
    phone_verified  = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    is_admin        = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        Group, blank=True, related_name='listings_users',
    )
    user_permissions = models.ManyToManyField(
        Permission, blank=True, related_name='listings_users',
    )

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = ['full_name']
    objects         = UserManager()

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        ordering            = ['-created_at']


# ── Business models ───────────────────────────────────────────────────────────

class PaymentMethod(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash',     'Cash'),
        ('transfer', 'Transfer'),
        ('pos',      'POS'),
    ]
    name = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name        = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering            = ['name']


class Listing(models.Model):
    CATEGORY_CHOICES = [
        ('hotel',         'Hotel'),
        ('restaurant',    'Restaurant'),
        ('bukka',         'Bukka'),
        ('bar',           'Bar'),
        ('shop',          'Shop'),
        ('recreation',    'Recreational Places'),
        ('hair_salon',    'Hair Salon'),
        ('barbing_salon', 'Barbing Salon'),
        ('pharmacy',      'Pharmacy'),
        ('local_market',  'Local Market'),
        ('supermarket',   'Supermarket'),
    ]
    name              = models.CharField(max_length=200)
    slug              = models.SlugField(max_length=200, unique=True, blank=True)
    category          = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    address           = models.CharField(max_length=300)
    landmark          = models.CharField(max_length=300, blank=True)
    phone1            = models.CharField(max_length=20)
    phone2            = models.CharField(max_length=20, blank=True)
    website           = models.URLField(max_length=200, blank=True)
    description       = models.TextField(blank=True)
    price_min         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Starting price or single price')
    price_max         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Upper price (leave blank for single price)')
    checkin_time      = models.TimeField(null=True, blank=True, help_text='Hotels only')
    checkout_time     = models.TimeField(null=True, blank=True, help_text='Hotels only')
    accepted_payments = models.ManyToManyField(PaymentMethod, blank=True)
    youtube_url       = models.URLField(max_length=200, blank=True, help_text='YouTube video URL for this business (e.g. https://www.youtube.com/watch?v=abc123)')
    is_verified       = models.BooleanField(default=False)
    is_active         = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.price_max is not None and self.price_min is None:
            raise ValidationError({'price_max': 'Cannot set a max price without a min price.'})
        if self.price_min is not None and self.price_max is not None:
            if self.price_max < self.price_min:
                raise ValidationError({'price_max': 'Max price cannot be less than min price.'})

    @property
    def price_display(self):
        if self.price_min is not None and self.price_max is not None:
            return f"₦{self.price_min:,.0f} – ₦{self.price_max:,.0f}"
        elif self.price_min is not None:
            return f"₦{self.price_min:,.0f}"
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug, n = base, 1
            while Listing.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def average_rating(self):
        reviews = self.reviews.filter(is_flagged=False)
        if reviews.exists():
            return round(sum(r.star_rating for r in reviews) / reviews.count(), 1)
        return None

    def is_open_now(self):
        now = timezone.localtime()
        day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        today = day_map[now.weekday()]
        try:
            h = self.hours.get(day=today)
            if h.is_closed:
                return False
            if h.open_time and h.close_time:
                return h.open_time <= now.time() <= h.close_time
            return False
        except OperatingHours.DoesNotExist:
            return False

    def get_user_claim(self, user):
        if not user or not user.is_authenticated:
            return None
        return self.claims.filter(user=user).first()

    def get_youtube_embed_url(self):
        if not self.youtube_url:
            return None
        url = self.youtube_url
        video_id = None
        if 'watch?v=' in url:
            video_id = url.split('watch?v=')[-1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0]
        elif 'youtube.com/embed/' in url:
            return url
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
        return None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Listing'
        verbose_name_plural = 'Listings'
        ordering            = ['-created_at']


class OperatingHours(models.Model):
    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'),
    ]
    listing    = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='hours')
    day        = models.CharField(max_length=3, choices=DAY_CHOICES)
    open_time  = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed  = models.BooleanField(default=False)

    def __str__(self):
        if self.is_closed:
            return f"{self.listing.name} — {self.get_day_display()}: Closed"
        return f"{self.listing.name} — {self.get_day_display()}: {self.open_time}–{self.close_time}"

    class Meta:
        unique_together     = ('listing', 'day')
        verbose_name        = 'Operating Hour'
        verbose_name_plural = 'Operating Hours'
        ordering            = ['listing', 'day']


class HotelFacility(models.Model):
    FACILITY_TYPE_CHOICES = [
        ('pool', 'Pool'), ('gym', 'Gym'), ('spa', 'Spa'),
        ('parking', 'Parking'), ('conference', 'Conference Room'),
        ('bar', 'Bar'), ('other', 'Other'),
    ]
    listing       = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='facilities')
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPE_CHOICES)
    name          = models.CharField(max_length=150)
    description   = models.TextField(max_length=300, blank=True)
    is_active     = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Facility'
        verbose_name_plural = 'Facilities'
        ordering            = ['facility_type']


class Photo(models.Model):
    PHOTO_TYPE_CHOICES = [
        ('interior', 'Interior'), ('exterior', 'Exterior'), ('room', 'Room'),
        ('facility', 'Facility'), ('activity', 'Activity'),
    ]
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    listing     = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    facility    = models.ForeignKey(HotelFacility, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    media_type  = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')
    image       = models.ImageField(upload_to='listings/photos/', null=True, blank=True)
    video_url   = models.URLField(max_length=200, blank=True, help_text='YouTube video URL for gallery (images: leave blank)')
    photo_type  = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES)
    caption     = models.CharField(max_length=200, blank=True)
    sort_order  = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.listing and self.facility:
            raise ValidationError('Photo can belong to a listing or facility, not both.')
        if not self.listing and not self.facility:
            raise ValidationError('Photo must belong to a listing or facility.')
        if self.media_type == 'image' and not self.image:
            raise ValidationError('An image file is required for media type "image".')
        if self.media_type == 'video' and not self.video_url:
            raise ValidationError('A YouTube URL is required for media type "video".')

    def get_youtube_embed_url(self):
        if not self.video_url:
            return None
        url = self.video_url
        video_id = None
        if 'watch?v=' in url:
            video_id = url.split('watch?v=')[-1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0]
        elif 'youtube.com/embed/' in url:
            return url
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
        return None

    def get_youtube_thumbnail(self):
        embed_url = self.get_youtube_embed_url()
        if embed_url:
            video_id = embed_url.split('/embed/')[-1]
            return f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        return None

    def __str__(self):
        owner = self.listing or self.facility
        return f"{self.media_type} ({self.photo_type}) for {owner}"

    class Meta:
        verbose_name        = 'Photo'
        verbose_name_plural = 'Photos'
        ordering            = ['sort_order', '-uploaded_at']


class MenuItem(models.Model):
    listing          = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='menu_items', null=True, blank=True)
    facility         = models.ForeignKey(HotelFacility, on_delete=models.CASCADE, related_name='menu_items', null=True, blank=True)
    item_name        = models.CharField(max_length=150)
    description      = models.TextField(max_length=300, blank=True)
    price_min        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Starting price or single price')
    price_max        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Upper price (leave blank for single price)')
    price_updated_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.listing and self.facility:
            raise ValidationError('Menu item can belong to a listing or facility, not both.')
        if not self.listing and not self.facility:
            raise ValidationError('Menu item must belong to a listing or facility.')
        if self.price_max is not None and self.price_min is None:
            raise ValidationError({'price_max': 'Cannot set a max price without a min price.'})
        if self.price_min is not None and self.price_max is not None:
            if self.price_max < self.price_min:
                raise ValidationError({'price_max': 'Max price cannot be less than min price.'})

    @property
    def price_display(self):
        if self.price_min is not None and self.price_max is not None:
            return f"₦{self.price_min:,.0f} – ₦{self.price_max:,.0f}"
        elif self.price_min is not None:
            return f"₦{self.price_min:,.0f}"
        return None

    def __str__(self):
        return f"{self.item_name} — {self.listing or self.facility}"

    class Meta:
        verbose_name        = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering            = ['item_name']


class RoomType(models.Model):
    listing          = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='room_type')
    room_name        = models.CharField(max_length=150)
    price_per_night  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.room_name} — {self.listing.name}"

    class Meta:
        verbose_name        = 'Room Type'
        verbose_name_plural = 'Room Types'
        ordering            = ['room_name']


class Amenity(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='amenities')
    name    = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.name} — {self.listing.name}"

    class Meta:
        unique_together     = ('listing', 'name')
        verbose_name        = 'Amenity'
        verbose_name_plural = 'Amenities'
        ordering            = ['name']


class Activity(models.Model):
    listing          = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='activities')
    facility         = models.ForeignKey(HotelFacility, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    name             = models.CharField(max_length=150)
    price_min        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Starting price or single price')
    price_max        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Upper price (leave blank for single price)')
    price_updated_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.facility and self.facility.listing != self.listing:
            raise ValidationError("Activity's facility must belong to the same listing.")
        if self.price_max is not None and self.price_min is None:
            raise ValidationError({'price_max': 'Cannot set a max price without a min price.'})
        if self.price_min is not None and self.price_max is not None:
            if self.price_max < self.price_min:
                raise ValidationError({'price_max': 'Max price cannot be less than min price.'})

    @property
    def price_display(self):
        if self.price_min is not None and self.price_max is not None:
            return f"₦{self.price_min:,.0f} – ₦{self.price_max:,.0f}"
        elif self.price_min is not None:
            return f"₦{self.price_min:,.0f}"
        return None

    def __str__(self):
        return f"{self.name} — {self.facility or self.listing}"

    class Meta:
        verbose_name        = 'Activity'
        verbose_name_plural = 'Activities'
        ordering            = ['name']


class Product(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='products')
    name    = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.name} — {self.listing.name}"

    class Meta:
        unique_together     = ('listing', 'name')
        verbose_name        = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering            = ['name']


class ListingClaim(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    ROLE_CHOICES = [
        ('owner',          'Owner'),
        ('manager',        'Manager'),
        ('staff',          'Staff member'),
        ('representative', 'Representative'),
    ]
    VERIFICATION_CHOICES = [
        ('business_phone', 'Business phone number'),
        ('cac',            'CAC registration number'),
        ('other',          'Other'),
    ]
    listing             = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='claims')
    user                = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='claims')
    full_name           = models.CharField(max_length=100)
    phone               = models.CharField(max_length=20)
    role                = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='business_phone')
    business_phone      = models.CharField(max_length=20, blank=True)
    note                = models.TextField(blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note          = models.TextField(null=True, blank=True)
    claimed_at          = models.DateTimeField(auto_now_add=True)
    reviewed_at         = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Claim by {self.user} for {self.listing.name}"

    class Meta:
        unique_together     = ('listing', 'user')
        verbose_name        = 'Listing Claim'
        verbose_name_plural = 'Listing Claims'
        ordering            = ['-claimed_at']


class VerifiedTier(models.Model):
    listing     = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='verified_tiers')
    payment_ref = models.CharField(max_length=100, unique=True)
    start_date  = models.DateField()
    end_date    = models.DateField()
    is_active   = models.BooleanField(default=True)
    badge_image = models.ImageField(upload_to='listings/badges/')
    created_at  = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.end_date < timezone.now().date()

    def __str__(self):
        return f"{self.listing.name} — verified until {self.end_date}"

    class Meta:
        verbose_name        = 'Verified Tier'
        verbose_name_plural = 'Verified Tiers'
        ordering            = ['-created_at']


class Review(models.Model):
    listing     = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    star_rating = models.PositiveIntegerField(choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)])
    comment     = models.TextField(max_length=500, blank=True)
    is_flagged  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} → {self.listing.name} ({self.star_rating}★)"

    class Meta:
        unique_together     = ('listing', 'user')
        verbose_name        = 'Review'
        verbose_name_plural = 'Reviews'
        ordering            = ['-created_at']


class Service(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='services')
    name    = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.name} — {self.listing.name}"

    class Meta:
        unique_together     = ('listing', 'name')
        verbose_name        = 'Service'
        verbose_name_plural = 'Services'
        ordering            = ['name']