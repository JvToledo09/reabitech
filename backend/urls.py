from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect, render

def home(request):
    return redirect('/dashboard/')

def dashboard(request):
    return render(request, 'dashboard.html')

urlpatterns = [
    path('', home),

    path('admin/', admin.site.urls),

    path('dashboard/', dashboard),

    path('atletas/', include('atletas.urls')),
]