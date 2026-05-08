from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', lambda request: render(request,'home.html')),

    path('dashboard/', lambda request: render(request,'dashboard.html')),

    path('atletas/', include('atletas.urls')),

]