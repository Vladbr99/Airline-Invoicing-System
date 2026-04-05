from django.contrib import admin
from .models import Customer, Flight, Invoice, InvoiceItem, UserProfile

admin.site.register(Customer)
admin.site.register(Flight)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(UserProfile)
