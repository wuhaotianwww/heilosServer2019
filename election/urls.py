from django.urls import path
from . import views

urlpatterns = [
    path('createElection/', views.create_election),
    path('fetchElections/', views.fetch_elections),
    path('updateElection/', views.update_elections),
    path('deleteElection/', views.delete_elections),

    path('startElection/', views.start_voting),
    path('freezeElection/', views.suspend_voting),
    path('endElection/', views.stop_voting),
    path('resultElection/', views.generate_result),
    path('fetchBbs/', views.response_bbc),

    path('fetchVotings/', views.fetch_vote_info),
    path('fetchVotingInfo/', views.fetch_vote_functions),
    path('reportVoting/', views.collect_votes),

    path('download/<str:file_path>/', views.file_response_download)
]
