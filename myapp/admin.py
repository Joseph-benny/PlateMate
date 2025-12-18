from django.contrib import admin

from .models import *
admin.site.register(Register)
admin.site.register(Menu)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Sale)
admin.site.register(SpecialOffer)
admin.site.register(ComboOffer)
admin.site.register(SpecialOfferCart)
admin.site.register(ComboOfferCart)

# Register your models here.
