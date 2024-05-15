
import json
import bcrypt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User


@csrf_exempt
def users(request):
    if request.method != 'POST':
        return JsonResponse({"error": "HTTP method not supported"}, status=405)
    
    try:
        body_json = json.loads(request.body)
        json_username = body_json['name']
        json_email = body_json['mail']
        json_password = body_json['password']
        json_birthdate = body_json['birthdate']
    except KeyError:
        return JsonResponse({"error": "Missing parameter in body"}, status=400)
    
    if '@' not in json_email or len(json_email) < 5:
        return JsonResponse({"error": "Invalid email"}, status=400)
    
    try:
        repeat_user = User.objects.get(email=json_email)
    except User.DoesNotExist:
        pass
    else:
        return JsonResponse({"error": "Email already exists"}, status=400)
    
    salted_and_hashed_pass = bcrypt.hashpw(json_password.encode('utf8'), bcrypt.gensalt()).decode('utf8')
    user_object = User(name=json_username, email=json_email, encrypted_password=salted_and_hashed_pass, birthdate=json_birthdate)
    user_object.save()

    return JsonResponse({"registered": True}, status=200)
    