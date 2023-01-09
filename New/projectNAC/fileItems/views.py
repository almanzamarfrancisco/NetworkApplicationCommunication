from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from datetime import datetime
from django.template import loader

from fileItems.models import FileItem

def HomeView(request):
	template = loader.get_template('fileItems/base.html')
	context = {}
	return HttpResponse(template.render(context, request))