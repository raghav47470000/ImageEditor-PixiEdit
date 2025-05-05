from django.db import models

class Image(models.Model):
    original_image = models.ImageField(upload_to='images/original/')
    edited_image = models.ImageField(upload_to='images/edited/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id}"