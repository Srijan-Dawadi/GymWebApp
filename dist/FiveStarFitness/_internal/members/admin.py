from django.contrib import admin
from .models import Member, MembershipPlan

admin.site.register(MembershipPlan)
admin.site.register(Member)
