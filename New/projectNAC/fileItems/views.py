from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from datetime import datetime
from django.template import loader
from .forms import UploadFileForm
from django.conf import settings
import json
import os

from fileItems.models import FileItem

def handle_uploaded_file(f):
	print(os.path.join(settings.MEDIA_ROOT, "fileItems/" + f.name))
	with open(os.path.join(settings.MEDIA_ROOT, "fileItems/" + f.name), 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

def home_view(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			handle_uploaded_file(request.FILES['formFile'])
			return HttpResponseRedirect('home')
	# else:
	template = loader.get_template('fileItems/base.html')
	context = {}
	return HttpResponse(template.render(context, request))
# def upload_file(request):
# 	if request.method == 'POST':
# 		form = UploadFileForm(request.POST, request.FILES)
# 		if form.is_valid():
# 			print(json.dumps(request))
# 			handle_uploaded_file(request.FILES['file'])
# 			return HttpResponseRedirect('')
# 	else:
# 		form = UploadFileForm()
# 	return render(request, 'upload.html', {'form': form})
