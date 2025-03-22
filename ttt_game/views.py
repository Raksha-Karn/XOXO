from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import SignUpForm


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
        form = SignUpForm(request.POST or None)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, "Registration Successful")
            return redirect('index')
        else:
            messages.error(request, "Something went wrong! Please try again.")
            return redirect('register')
    else:
        form = SignUpForm()
        return render(request, "ttt_game/register.html", {'form': form})