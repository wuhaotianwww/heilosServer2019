from django.contrib import admin
from .models import Elections, VoterList


class ElectionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'startTime', 'endTime', 'status', 'id')
    list_filter = ('startTime', 'author')
    search_fields = ('shortName',)
    date_hierarchy = 'startTime'
    ordering = ['-startTime', 'author']


admin.site.register(Elections, ElectionsAdmin)
admin.site.register(VoterList)

# Register your models here.
