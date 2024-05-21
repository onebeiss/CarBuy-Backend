
import json
import bcrypt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User
import secrets


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
    
@csrf_exempt    
def sessions(request):
    if request.method == 'POST': #Ejemplo: curl -X POST -d "{\"email\": \"jose@mail.com\", \"password\": \"1234\"}" http://localhost:8000/sessions/
        try: # Análisis del JSON de la solicitud y extracción del correo electrónico y la contraseña
            body_json = json.loads(request.body)
            json_email = body_json['email']
            json_password = body_json['password']
        except KeyError: #Devuelve un error si falta algún parámetro en el cuerpo de la solicitud realizada por el usuario
            return JsonResponse({"error": "Request error or invalid data"}, status=400)
        
        try: #Obtención de un usuario de la base de datos usando el correo electrónico
            db_user = User.objects.get(email=json_email)
        except User.DoesNotExist: 
            return JsonResponse({"error": "User not in database"}, status=404) #Devuelve un error si el usario no se encuentra en la base de datos
        if bcrypt.checkpw(json_password.encode('utf8'), db_user.encrypted_password.encode('utf8')): # Verifica la contraseña proporcionada con la contraseña almacenada en la base de datos usando bcrypt
            pass
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        
        random_token = secrets.token_hex(10) # Genera un token aleatorio para la sesión
        db_user.token = random_token #Guardo el token de sesion en la base de datos
        db_user.save()  #Guardo la sesion
        return JsonResponse({"sessionToken": random_token}, status=200) # Devuelve una respuesta exitosa con el token generado
    
    elif request.method == 'DELETE': #Ejemplo: curl -X DELETE -H "sessionToken: f0a55bd78563389cc536" http://localhost:8000/sessions/
        try:
            header_token = request.headers.get("sessionToken", None) #Obtención del token de sesión del encabezado de la solicitud
        except AttributeError: #Si hay error...
            return JsonResponse({"error": "Body token missing"}, status=401)
        session = User.objects.get(token=header_token) # Intenta obtener la sesión de usuario basada en el token alojada en la base de datos
        session.token = None
        session.save() #Se elimina
        return JsonResponse({"message": "Session closed successfully"}, status=200)
    
@csrf_exempt
def password(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'HTTP method not supported'}, status=405)

    # Obtener el cuerpo de la solicitud JSON
    try:
        body_json = json.loads(request.body)
        current_password = body_json['current_password']
        new_password = body_json['new_password']
    except KeyError:
        return JsonResponse({'error': 'Missing parameter in body'}, status=400)

    try:
        sessionToken = request.headers['sessionToken']  #Obtenemos el token de sesión mediante el headers
    except AttributeError:
        return JsonResponse({'error': 'Header token missing'})
    
    # Obtener el usuario con el token de sesión proporcionado
    try:
        user = User.objects.get(token=sessionToken)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid sessionToken'}, status=401)

    # Verificar la contraseña actual
    if not bcrypt.checkpw(current_password.encode('utf8'), user.encrypted_password.encode('utf8')):
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    # Generar el hash para la nueva contraseña
    hashed_new_password = bcrypt.hashpw(new_password.encode('utf8'), bcrypt.gensalt()).decode('utf8')

    # Actualizar la contraseña del usuario
    user.encrypted_password = hashed_new_password
    user.save()

    return JsonResponse({'message': 'Password changed succesfully'}, status=200)