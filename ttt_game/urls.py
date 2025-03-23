from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("games/", views.game_list, name="game_list"),
    path("games/create/", views.create_game, name="create_game"),
    path("games/<int:game_id>/join/", views.join_game, name="join_game"),
    path("games/<int:game_id>/", views.game_detail, name="game_detail"),
]