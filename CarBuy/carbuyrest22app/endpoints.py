
import json
import bcrypt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Car, User
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
        json_phone = body_json['phone']
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
    user_object = User(name=json_username, email=json_email, encrypted_password=salted_and_hashed_pass, birthdate=json_birthdate, phone=json_phone)
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
    
    elif request.method == 'DELETE': #Ejemplo: curl -X DELETE -H "sessionToken: 922aa6990578697f7afc" http://localhost:8000/sessions/
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
    
    # Obtener el token de sesión del encabezado
    sessionToken = request.headers.get('sessionToken')
    
    # Verificar si el token de sesión está presente
    if not sessionToken:
        return JsonResponse({'error': 'Header token missing'}, status=401)  # curl -X POST -H "Content-Type: application/json" -d "{\"current_password\": \"Carmenchu10\", \"new_password\": \"CCarmenchu10\"}"  http://localhost:8000/password/
    
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

    return JsonResponse({'message': 'Password changed succesfully'}, status=200)    # curl -X POST http://localhost:8000/password/ -H "Content-Type: application/json" -H "sessionToken: 51fde779db0a0b3e1bcd" -d '{"current_password": "1234", "new_password": "123456789"}'

@csrf_exempt
def account(request):
    if request.method == 'GET': # curl -X GET http://localhost:8000/account -H "sessionToken: 922aa6990578697f7afc"
        # Obtener el token de sesión de la cabecera
        header_token = request.headers.get('sessionToken', None)

        # Recuperamos token de la cabecera
        if not header_token:
            return JsonResponse({'error': 'Body token missing'}, status=401)
        # Recupera la sesión del usuario correspondiente al token pasado en la bbdd
        session = User.objects.get(token=header_token) 
        json_response = session.to_jsonAccount() 
        return JsonResponse(json_response, status=200)
    
@csrf_exempt
def search_cars(request):
    if request.method == 'GET':
        # Obtener el nombre de la marca de coche de los parámetros de la solicitud
        brand_name = request.GET.get('brand_name', None)
        
        # Verificar si se proporcionó un nombre de marca de coche
        if not brand_name:
            return JsonResponse({'error': 'Brand name missing'}, status=400)
        
        # Realizar la búsqueda en la base de datos por el nombre de la marca de coche
        cars = Car.objects.filter(brand__icontains=brand_name)
        
        # Convertir los resultados a un formato JSON
        results = []
        for car in cars:
            car_data = {
                'brand': car.brand,
                'model': car.model,
                'year': car.year,
                'price': str(car.price),
                'description': car.description,
                'user_id': car.user_id
            }
            results.append(car_data)
        
        # Retornar los resultados como una respuesta JSON
        return JsonResponse({'cars': results}, status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, Car

@csrf_exempt
def ad_details(request, position_id):
    if request.method == 'GET':  # Ejemplo: curl -X GET http://localhost:8000/ad/1/
        try:
            # Obtener el coche en la posición especificada
            car = Car.objects.get(id=position_id)
        except IndexError:
            return JsonResponse({"error": "Ad not found"}, status=404)

        # Obtener el usuario asociado a este coche
        user = car.user
        
        # Crear la respuesta JSON
        user_data = {
            "name": user.name,
            "phone": user.phone
        }
        
        car_data = {
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "price": car.price,
            "description": car.description,
            "user": user_data
        }

        return JsonResponse(car_data, status=200)
    
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
@csrf_exempt
def ad_management(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        brand = data.get("brand")
        model = data.get("model")
        year = data.get("year")
        price = data.get("price")
        description = data.get("description")
        user_id = data.get("user_id")
        
        if not all([brand, model, year, price, description, user_id]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        
        car = Car.objects.create(
            brand=brand,
            model=model,
            year=year,
            price=price,
            description=description,
            user=user
        )
        
        return JsonResponse({"message": "Ad created successfully"}, status=201)
    
