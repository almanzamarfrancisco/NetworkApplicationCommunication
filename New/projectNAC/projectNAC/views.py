# Django
from django.http import HttpResponse
from django.http import JsonResponse
# Utilities
from datetime import datetime


def hellow_world(request):
	now = datetime.now().strftime('%b %dth. %y - %H:%M hrs')
	return HttpResponse(
		'<h1>Hello, world!</h1><br> current time is {now}'
			.format(now=str(now))
		)
def sort_integers(request):
	# import pdb;pdb.set_trace()#
	# print(request.get)
	if 'numbers' in request.GET:
		numbers = [int(number) for number in request.GET['numbers'].split(',')]
		numbers.sort()
		return JsonResponse({'numbers': numbers})
	else:
		return HttpResponse('For this url works you must put a get param named numbers with integers for sorting them')
def say_hi(request, name, age):
	if age < 12:
		message = 'Sorry {}, you are not allowed here'.format(name)
	else:
		message = 'Hello, {}!, welcome to platzigram'.format(name)
	return HttpResponse('<h1>{}</h1>'.format(message))
