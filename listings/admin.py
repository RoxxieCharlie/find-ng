from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Listing, PaymentMethod, HotelFacility,
    OperatingHours, Photo, MenuItem, RoomType,
    Amenity, Activity, Product, Service,
    ListingClaim, Review, VerifiedTier,
)


# ── User admin ────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display      = ('full_name', 'phone', 'phone_verified', 'is_active', 'is_staff', 'created_at')
    list_filter       = ('phone_verified', 'is_active', 'is_staff', 'is_admin')
    search_fields     = ('full_name', 'phone')
    ordering          = ('-created_at',)
    readonly_fields   = ('created_at',)
    filter_horizontal = ()

    fieldsets = (
        ('Personal info', {'fields': ('full_name', 'phone', 'password')}),
        ('Verification',  {'fields': ('phone_verified',)}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_admin')}),
        ('Dates',         {'fields': ('created_at',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('phone', 'full_name', 'password1', 'password2'),
        }),
    )


# ── Inlines ───────────────────────────────────────────────────────────────────

class OperatingHoursInline(admin.TabularInline):
    model    = OperatingHours
    extra    = 7
    ordering = ['day']


class PhotoInline(admin.TabularInline):
    model  = Photo
    extra  = 1
    fields = ('media_type', 'image', 'video_url', 'photo_type', 'caption', 'sort_order')


class MenuItemInline(admin.TabularInline):
    model  = MenuItem
    extra  = 1
    fields = ('item_name', 'description', 'price_min', 'price_max', 'price_updated_at')


class RoomTypeInline(admin.TabularInline):
    model  = RoomType
    extra  = 1
    fields = ('room_name', 'price_per_night', 'price_updated_at')


class AmenityInline(admin.TabularInline):
    model  = Amenity
    extra  = 1
    fields = ('name',)


class ServiceInline(admin.TabularInline):
    model  = Service
    extra  = 1
    fields = ('name',)


class ActivityInline(admin.TabularInline):
    model  = Activity
    extra  = 1
    fields = ('name', 'price_min', 'price_max', 'price_updated_at')


class ProductInline(admin.TabularInline):
    model  = Product
    extra  = 1
    fields = ('name',)


class HotelFacilityInline(admin.StackedInline):
    model  = HotelFacility
    extra  = 0
    fields = ('facility_type', 'name', 'description', 'is_active')


class VerifiedTierInline(admin.StackedInline):
    model  = VerifiedTier
    extra  = 0
    fields = ('payment_ref', 'start_date', 'end_date', 'is_active')


class FacilityPhotoInline(admin.TabularInline):
    model  = Photo
    extra  = 1
    fields = ('media_type', 'image', 'video_url', 'photo_type', 'caption', 'sort_order')


class FacilityMenuItemInline(admin.TabularInline):
    model  = MenuItem
    extra  = 1
    fields = ('item_name', 'description', 'price_min', 'price_max', 'price_updated_at')


class FacilityActivityInline(admin.TabularInline):
    model  = Activity
    extra  = 1
    fields = ('name', 'price_min', 'price_max', 'price_updated_at')


# ── Model admins ──────────────────────────────────────────────────────────────

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display        = ('name', 'category', 'address', 'phone1', 'is_verified', 'is_active', 'created_at')
    list_filter         = ('category', 'is_verified', 'is_active')
    search_fields       = ('name', 'address', 'landmark', 'phone1')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields     = ('created_at', 'updated_at')
    filter_horizontal   = ('accepted_payments',)
    ordering            = ('-is_verified', '-created_at')

    fieldsets = (
        ('Basic info',  {'fields': ('name', 'slug', 'category', 'description')}),
        ('Location',    {'fields': ('address', 'landmark')}),
        ('Contact',     {'fields': ('phone1', 'phone2', 'website')}),
        ('Pricing',     {'fields': ('price_min', 'price_max')}),
        ('Services',    {'fields': ('accepted_payments',)}),
        ('Media',       {'fields': ('youtube_url',)}),
        ('Hotel only',  {'classes': ('collapse',), 'fields': ('checkin_time', 'checkout_time')}),
        ('Status',      {'fields': ('is_verified', 'is_active')}),
        ('Timestamps',  {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    inlines = [
        OperatingHoursInline, PhotoInline, MenuItemInline, RoomTypeInline,
        AmenityInline, ActivityInline, ProductInline, ServiceInline,
        HotelFacilityInline, VerifiedTierInline,
    ]


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')

    def display_name(self, obj):
        return obj.get_name_display()
    display_name.short_description = 'Display name'


@admin.register(HotelFacility)
class HotelFacilityAdmin(admin.ModelAdmin):
    list_display  = ('name', 'facility_type', 'listing', 'is_active')
    list_filter   = ('facility_type', 'is_active')
    search_fields = ('name', 'listing__name')
    inlines       = [FacilityPhotoInline, FacilityMenuItemInline, FacilityActivityInline]


@admin.register(ListingClaim)
class ListingClaimAdmin(admin.ModelAdmin):
    list_display    = ('listing', 'user', 'status', 'claimed_at', 'reviewed_at')
    list_filter     = ('status',)
    search_fields   = ('listing__name', 'user__full_name', 'user__phone')
    ordering        = ('-claimed_at',)
    readonly_fields = ('claimed_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ('listing', 'user', 'star_rating', 'is_flagged', 'created_at')
    list_filter     = ('star_rating', 'is_flagged')
    search_fields   = ('listing__name', 'user__full_name')
    ordering        = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(VerifiedTier)
class VerifiedTierAdmin(admin.ModelAdmin):
    list_display    = ('listing', 'start_date', 'end_date', 'is_active', 'payment_ref')
    list_filter     = ('is_active',)
    search_fields   = ('listing__name', 'payment_ref')
    ordering        = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ('name', 'listing')
    search_fields = ('name', 'listing__name')
    ordering      = ('listing', 'name')