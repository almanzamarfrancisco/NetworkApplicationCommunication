from django.db import models

class FileItem(models.Model):
	name = models.CharField(max_length=255)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)
# admin.site.register(FileItem)
