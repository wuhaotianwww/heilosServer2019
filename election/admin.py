from django.contrib import admin
from .models import Elections, VoterList


# class ElectionsAdmin(admin.ModelAdmin):
#     list_display = ('name', 'author', 'startTime', 'endTime', 'status', 'id')
#     list_filter = ('startTime', 'author')
#     search_fields = ('shortName',)
#     date_hierarchy = 'startTime'
#     ordering = ['-startTime', 'author']


admin.site.register(Elections)
admin.site.register(VoterList)

# Register your models here.  python manage.py createsuperuser
# python manage.py makemigrations election
# python manage.py migrate
# python manage.py runserver localhost:8888
