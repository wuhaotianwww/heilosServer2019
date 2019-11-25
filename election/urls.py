from django.urls import path
from . import views

urlpatterns = [
    path('createElection/', views.create_election),
    path('fetchElections/', views.fetch_elections),
    path('updateElection/', views.update_elections),
    path('deleteElection/', views.delete_elections),

    path('startElection/', views.delete_elections),
    path('freezeElection/', views.delete_elections),
    path('endElection/', views.delete_elections),
    path('resultElection/', views.delete_elections),
    path('fetchBbs/', views.delete_elections),

    path('fetchVotings/', views.delete_elections),
    path('fetchVotingInfo/', views.fetch_voters),
    path('reportVoting/', views.delete_elections)
]
