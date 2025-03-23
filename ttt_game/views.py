from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game
from django.db import models
from .forms import SignUpForm
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json


def index(request):
    if request.user.is_authenticated:
        return render(request, "ttt_game/index.html")
    else:
        return redirect('login')

def login_user(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already logged in!")
        return redirect('index')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful")
            return redirect('index')
        else:
            messages.error(request, "Something went wrong! Please try again.")
            return redirect('login')
        
    return render(request, "ttt_game/login.html")

def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logout Successful")
        return redirect('login')
    else:
        messages.error(request, "You are not logged in!")
        return redirect('login')

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, "Registration Successful")
            return redirect('index')
        else:
            return render(request, "ttt_game/register.html", {'form': form})
    else:
        form = SignUpForm()
    return render(request, "ttt_game/register.html", {'form': form})
    
@login_required
def game_list(request):
    active_games = Game.objects.filter(
        status__in=['active', 'waiting']
    ).order_by('-created_at')
    
    my_games = active_games.filter(
        models.Q(player_x=request.user) | models.Q(player_o=request.user)
    )
    
    available_games = active_games.filter(
        status='waiting'
    ).exclude(player_x=request.user)
    
    return render(request, "ttt_game/game_list.html", {
        'my_games': my_games,
        'available_games': available_games
    })
    
@login_required
def create_game(request):
    game = Game.objects.create(player_x=request.user)
    
    channel_layer = get_channel_layer()
    game_data = {
        'id': game.id,
        'status': game.status,
        'current_player': game.current_player,
        'player_x': request.user.username,
        'player_o': None,
    }
    
    async_to_sync(channel_layer.group_send)(
        'game_list',
        {
            'type': 'game_list_update',
            'action': 'create',
            'game': game_data
        }
    )
    
    return redirect('game_detail', game_id=game.id)

@login_required
def join_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.join_game(request.user):
        game_state = {
            'board': game.board,
            'current_player': game.current_player,
            'status': game.status,
            'winner': game.winner,
            'player_x': game.player_x.username if game.player_x else None,
            'player_o': request.user.username,
        }
        
        channel_layer = get_channel_layer()
        game_data = {
            'id': game.id,
            'status': game.status,
            'current_player': game.current_player,
            'player_x': game.player_x.username if game.player_x else None,
            'player_o': request.user.username,
        }
        
        async_to_sync(channel_layer.group_send)(
            'game_list',
            {
                'type': 'game_list_update',
                'action': 'update',
                'game': game_data
            }
        )
        
        async_to_sync(channel_layer.group_send)(
            f'game_{game_id}',
            {
                'type': 'game_update',
                'state': game_state
            }
        )
        
        return redirect('game_detail', game_id=game.id)
    else:
        return redirect('game_list')
    
@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return render(request, "ttt_game/game_detail.html", {
        'game': game,
        'game_id': game.id,
        'board': json.loads(game.board)
    })