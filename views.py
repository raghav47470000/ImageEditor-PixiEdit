from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Image
from .forms import ImageUploadForm
from PIL import Image as PILImage, ImageOps, ImageEnhance, ImageFilter
import os
from django.conf import settings
import requests
from .forms import FeedbackForm



def about(request):
    return render(request, 'my_app/about.html')


# Home View
def home(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            return redirect('my_app:edit_image', image_id=image.id)
    else:
        form = ImageUploadForm()
    images = Image.objects.all()
    return render(request, 'my_app/home.html', {'form': form, 'images': images})


# Upload Image View
def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('my_app:home')  # Redirect to the home page after successful upload
    else:
        form = ImageUploadForm()
    return render(request, 'my_app/upload_image.html', {'form': form})


# Edit Image View
def edit_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        pil_image = PILImage.open(image.original_image.path)

        try:
            # Features accessible to all users
            if action == 'grayscale':
                edited_image = ImageOps.grayscale(pil_image)
            elif action == 'rotate':
                rotate_angle = int(request.POST.get('rotate_angle', 90))  # Default to 90 degrees
                edited_image = pil_image.rotate(rotate_angle, expand=True)
            elif action == 'resize':
                resize_width = int(request.POST.get('resize_width', 300))  # Default width
                resize_height = int(request.POST.get('resize_height', 300))  # Default height
                edited_image = pil_image.resize((resize_width, resize_height))
            elif action == 'flip':
                flip_direction = request.POST.get('flip_direction', 'horizontal')
                if flip_direction == 'horizontal':
                    edited_image = pil_image.transpose(PILImage.FLIP_LEFT_RIGHT)
                elif flip_direction == 'vertical':
                    edited_image = pil_image.transpose(PILImage.FLIP_TOP_BOTTOM)
                else:
                    edited_image = pil_image

            # Features restricted to logged-in users
            elif action in ['brightness', 'contrast', 'saturation', 'blur', 'crop', 'sharpen']:
                if not request.user.is_authenticated:
                    return HttpResponse("You must be logged in to access this feature.", status=403)

                if action == 'brightness':
                    brightness_factor = float(request.POST.get('brightness_factor', 1.0))  # Default to 1.0
                    enhancer = ImageEnhance.Brightness(pil_image)
                    edited_image = enhancer.enhance(brightness_factor)
                elif action == 'contrast':
                    contrast_factor = float(request.POST.get('contrast_factor', 1.0))  # Default to 1.0
                    enhancer = ImageEnhance.Contrast(pil_image)
                    edited_image = enhancer.enhance(contrast_factor)
                elif action == 'saturation':
                    saturation_factor = float(request.POST.get('saturation_factor', 1.0))  # Default to 1.0
                    enhancer = ImageEnhance.Color(pil_image)
                    edited_image = enhancer.enhance(saturation_factor)
                elif action == 'blur':
                    blur_radius = float(request.POST.get('blur_radius', 2.0))  # Default to 2.0
                    edited_image = pil_image.filter(ImageFilter.GaussianBlur(blur_radius))
                elif action == 'crop':
                    # Get crop coordinates from POST request
                    left = int(request.POST.get('left', 0))
                    top = int(request.POST.get('top', 0))
                    right = int(request.POST.get('right', pil_image.width))
                    bottom = int(request.POST.get('bottom', pil_image.height))
                
                    # Validate coordinates
                    left = max(0, min(left, pil_image.width))
                    top = max(0, min(top, pil_image.height))
                    right = max(left, min(right, pil_image.width))  # Ensure right is greater than left
                    bottom = max(top, min(bottom, pil_image.height))  # Ensure bottom is greater than top
                
                    # Perform cropping
                    if left < right and top < bottom:
                        edited_image = pil_image.crop((left, top, right, bottom))
                    else:
                        raise ValueError("Invalid crop dimensions: ensure left < right and top < bottom.")               
                elif action == 'sharpen':
                    sharpness_factor = float(request.POST.get('sharpness_factor', 1.0))  # Default to 1.0
                    sharpness_factor = max(1.0, min(sharpness_factor, 10.0)) 
                    enhancer = ImageEnhance.Sharpness(pil_image)
                    edited_image = enhancer.enhance(sharpness_factor)
            else:
                edited_image = pil_image

            # Save the edited image
            edited_dir = os.path.join(settings.MEDIA_ROOT, 'images/edited/')
            os.makedirs(edited_dir, exist_ok=True)  # Ensure the directory exists
            edited_path = os.path.join(edited_dir, f'edited_{image.id}.png')
            edited_image.save(edited_path)
            image.edited_image = f'images/edited/edited_{image.id}.png'
            image.save()
        except Exception as e:
            return HttpResponse(f"Error processing image: {e}")

        return redirect('my_app:edit_image', image_id=image.id)

    return render(request, 'my_app/edit_image.html', {'image': image})


# Download Image View
def download_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    try:
        # Check if the edited image exists
        if image.edited_image:
            file_path = image.edited_image.path  # Use .path to get the file path
        else:
            file_path = image.original_image.path  # Use .path for the original image

        # Check if the file exists
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type="image/png")
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
        else:
            raise Http404("File not found.")
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

# Delete Image View
def delete_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    if request.method == 'POST':
        # Delete the image file from the filesystem
        if image.original_image:
            image.original_image.delete()
        if image.edited_image:
            image.edited_image.delete()
        # Delete the image object from the database
        image.delete()
        return redirect('my_app:home')  # Redirect to the home page after deletion
    return render(request, 'my_app/delete_image.html', {'image': image})


# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('my_app:home')  # Redirect to the home page
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'my_app/login.html')


# Signup View
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, 'Account created successfully')
            return redirect('my_app:login')  # Redirect to the login page
    return render(request, 'my_app/signup.html')


# Logout View
def logout_view(request):
    logout(request)
    return redirect('my_app:home')  # Redirect to the home page

from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import logging
from .forms import FeedbackForm

# Configure logging
logger = logging.getLogger(__name__)

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            data = {
                'username': request.user.username if request.user.is_authenticated else 'Anonymous',
                'comment': form.cleaned_data['comment']
            }
            try:
                # Send feedback to the external API
                response = requests.post('http://127.0.0.1:5001/api/feedback', json=data)
                if response.status_code == 200:
                    messages.success(request, 'Feedback submitted successfully.')
                else:
                    logger.error(f"Feedback API error: {response.status_code} - {response.text}")
                    messages.error(request, 'Error submitting feedback. Please try again later.')
            except requests.exceptions.RequestException as e:
                logger.error(f"Connection error with Feedback API: {e}")
                messages.error(request, 'Could not connect to the feedback service. Please try again later.')
            return redirect('my_app:feedback')
    else:
        form = FeedbackForm()

    return render(request, 'my_app/feedback.html', {'form': form})