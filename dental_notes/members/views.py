from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterUserForm
from .models import UserActivity

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # 记录登录活动
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            messages.success(request, ("Login Successful!"))
            return redirect('speech_index')
        else:
            messages.error(request, ("Invalid username or password - Please try again"))
            return redirect('login')
    else:
        return render(request, 'authenticate/login.html', {})

def logout_user(request):
    if request.user.is_authenticated:
        # 记录注销活动
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
    logout(request)
    messages.success(request, ("You Were Logged Out!"))
    return redirect('login')

def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自动登录新注册的用户
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration Successful!"))
            return redirect('speech_index')  # 使用 URL name 而不是路径
        else:
            messages.error(request, ("Registration Failed - Please correct the errors below"))
    else:
        form = RegisterUserForm()
    
    return render(request, 'authenticate/register.html', {
        'form': form,
    })