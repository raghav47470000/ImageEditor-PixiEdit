from django import forms
from .models import Image

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['original_image']


class FeedbackForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, label='Your Feedback')
