from django.urls import path
from . import views

urlpatterns = [
    path('createElection/', views.create_election),
    path('fetchElections/', views.fetch_elections),
    path('updateElection/', views.update_elections),
    path('deleteElection/', views.delete_elections),
    path('fetchVoters/', views.fetch_voters)
]
