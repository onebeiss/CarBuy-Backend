import json
import bcrypt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Car, FavouriteCar, User
import secrets


@csrf_exempt
def users(request):
    # curl -X POST -H "Content-Type: application/json" -d '{"name":"John Doe", "mail":"johndoe@example.com", "password":"password123", "birthdate":"2000-01-01", "phone":"123456789"}' http://localhost:8000/users/
    if request.method != 'POST':
        return JsonResponse({"error": "HTTP method not supported"}, status=405)
    
    try:
        # Intenta cargar el cuerpo de la solicitud como JSON
        body_json = json.loads(request.body)
        # Extrae los parámetros del JSON
        json_username = body_json['name']
        json_email = body_json['mail']
        json_password = body_json['password']
        json_birthdate = body_json['birthdate']
        json_phone = body_json['phone']
    except KeyError:
        # Si falta algún parámetro, devuelve un error
        return JsonResponse({"error": "Missing parameter in body"}, status=400)
    
    # Verifica que el correo electrónico sea válido
    if '@' not in json_email or len(json_email) < 5:
        return JsonResponse({"error": "Invalid email"}, status=400)
    
    try:
        # Verifica si ya existe un usuario con ese correo electrónico
        repeat_user = User.objects.get(email=json_email)
    except User.DoesNotExist:
        # Si no existe, continúa con el registro
        pass
    else:
        # Si el correo ya existe, devuelve un error
        return JsonResponse({"error": "Email already exists"}, status=400)
    
    # Hashea y saltea la contraseña
    salted_and_hashed_pass = bcrypt.hashpw(json_password.encode('utf8'), bcrypt.gensalt()).decode('utf8')
    # Crea un nuevo objeto de usuario con los datos proporcionados
    user_object = User(
        name=json_username,
        email=json_email,
        encrypted_password=salted_and_hashed_pass,
        birthdate=json_birthdate,
        phone=json_phone
    )
    # Guarda el nuevo usuario en la base de datos
    user_object.save()

    # Devuelve una respuesta indicando que el registro fue exitoso
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
        search_query = request.GET.get('q', None)
        
        # Verificar si se proporcionó un nombre de marca de coche
        if not search_query:
            return JsonResponse({'error': 'Search query missing'}, status=400)
        
        # Realizar la búsqueda en la base de datos por el nombre de la marca de coche
        cars = Car.objects.filter(brand__icontains=search_query) | Car.objects.filter(model__icontains=search_query)
        
        # Convertir los resultados a un formato JSON
        results = []
        for car in cars:
            car_data = {
                "car_id": car.id,
                'brand': car.brand,
                'model': car.model,
                'year': car.year,
                'price': str(car.price),
                'description': car.description,
                'image_url': car.image_url,
                'user_id': car.user_id
            }
            results.append(car_data)
        
        # Retornar los resultados como una respuesta JSON
        return JsonResponse({'cars': results}, status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def ad_details(request, position_id):
    if request.method == 'GET':
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
            "image_url": car.image_url,
            "user": user_data
        }

        return JsonResponse(car_data, status=200)
    
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
@csrf_exempt
def ad_management(request):
    # curl -X POST -H "Content-Type: application/json" -d '{"brand": "Volkswagen", "model": "Golf GTI", "year": 2006, "price": 9000, "description": "A good car to drive", "user_id": 1}' http://localhost:8000/ad_management/
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        # Guarda el contenido del json request
        brand = data.get("brand")
        model = data.get("model")
        year = data.get("year")
        price = data.get("price")
        description = data.get("description")
        image_url = data.get("image_url")
        user_id = data.get("user_id")
        
        # Comprueba que todas las variables tengan contenido
        if not all([brand, model, year, price, description, image_url, user_id]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        # Comprueba que el usuario exista
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        
        # Agrega un nuevo objeto con los datos del anuncio creado
        car = Car.objects.create(
            brand=brand,
            model=model,
            year=year,
            price=price,
            description=description,
            image_url=image_url,
            user=user
        )
        
        return JsonResponse({"message": "Ad created successfully"}, status=201)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        # Obtén el id del anuncio a actualizar
        car_id = data.get("car_id")
        
        # Comprueba que el id del anuncio tenga contenido
        if not car_id:
            return JsonResponse({"error": "car_id is required"}, status=400)
        
        # Comprueba que el anuncio exista
        try:
            car = Car.objects.get(id=car_id)
        except Car.DoesNotExist:
            return JsonResponse({"error": "Ad not found"}, status=404)
        
        # Actualiza los campos del anuncio con los datos proporcionados, si están presentes
        car.brand = data.get("brand", car.brand)
        car.model = data.get("model", car.model)
        car.year = data.get("year", car.year)
        car.price = data.get("price", car.price)
        car.description = data.get("description", car.description)
        car.image_url = data.get("image_url", car.image_url)
        car.user_id = data.get("user_id", car.user_id)
        
        # Guarda los cambios en la base de datos
        car.save()
        
        return JsonResponse({"message": "Ad updated successfully"}, status=200)
    
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        # Obtiene el id del anuncio a eliminar
        car_id = data.get("car_id")
        
        # Comprueba que el id del anuncio tenga contenido
        if not car_id:
            return JsonResponse({"error": "car_id is required"}, status=400)
        
        # Comprueba que el anuncio exista
        try:
            car = Car.objects.get(id=car_id)
        except Car.DoesNotExist:
            return JsonResponse({"error": "Ad not found"}, status=404)
        
        # Elimina el anuncio
        car.delete()
        
        return JsonResponse({"message": "Ad deleted successfully"}, status=200)
    
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
@csrf_exempt
def favourite_management(request):
    # curl -X PUT -H "Content-Type: application/json" -d '{"user_id": 2, "car_id": 5}' http://localhost:8000/favourite_management/
    if request.method != 'PUT':
        return JsonResponse({'error': 'HTTP method not supported'}, status=405)

    sessionToken = request.headers['sessionToken']
    if not sessionToken:
        return JsonResponse({'error': 'Missing sessionToken'}, status=400)
    
    try:
        user = User.objects.get(token=sessionToken)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid sessionToken'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    car_id = data.get('car_id')
    if not car_id:
        return JsonResponse({"error": "car_id is required"}, status=400)

    try:
        car_id = int(car_id)
    except ValueError:
        return JsonResponse({"error": "Invalid car_id"}, status=400)

    try:
        car_to_check = Car.objects.get(id=car_id)
    except Car.DoesNotExist:
        return JsonResponse({"error": "Car not found"}, status=404)

    # Verificar si el coche ya está en favoritos del usuario
    existing_favorite = FavouriteCar.objects.filter(user=user, car=car_to_check).exists()

    if existing_favorite:
        return JsonResponse({'success': False, 'message': 'Car is already in favourites'}, status=200)
    
    # Si no existe, agregarlo a favoritos
    favorite_car = FavouriteCar(user=user, car=car_to_check)
    favorite_car.save()

    return JsonResponse({'success': True, 'message': 'Car added to favourites'}, status=200)
    
@csrf_exempt
def get_favourites(request):
    # curl -X GET http://localhost:8000/get_favourites/
    if request.method == 'GET':

        sessionToken = request.headers['sessionToken']

        try:
            user = User.objects.get(token=sessionToken)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid sessionToken'}, status=401)
        
        # Obtiene los favoritos
        favourites = FavouriteCar.objects.filter(user=user)

        # Lista para almacenar los datos de favoritos
        favourites_data = []

        # Itera sobre los favoritos y agrega los datos a la lista
        for favourite in favourites:
            favourite_info = {
                "user_id": favourite.user.id,
                "car_id": favourite.car.id,
                "user_name": favourite.user.name,
                "car_brand": favourite.car.brand,
                "car_model": favourite.car.model,
                "car_year": favourite.car.year,
                "car_price": favourite.car.price,
                "car_description": favourite.car.description,
                "image_url": favourite.car.image_url
            }
            favourites_data.append(favourite_info)

        # Retorna la lista de datos de favoritos en formato JSON
        return JsonResponse(favourites_data, status=200, safe=False)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
def get_ads(request):
    # http://localhost:8000/get_ads/
    if request.method == 'GET':
        # Obtiene todos los anuncios de coches
        all_cars = Car.objects.all()

        # Lista para almacenar los datos
        cars_data = []

        # Itera sobre los coches y agrega los datos a la lista
        for car in all_cars:
            car_info = {
                "id": car.id,
                "brand": car.brand,
                "model": car.model,
                "year": car.year,
                "price": str(car.price),  # Convertir Decimal a String
                "description": car.description,
                "image_url": car.image_url,
                "user_id": car.user_id
            }
            cars_data.append(car_info)

        # Retorna la lista de datos en formato JSON
        return JsonResponse(cars_data, safe=False)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
@csrf_exempt
def get_user(request):
    # http://localhost:8000/get_user/
    if request.method == 'GET':

        sessionToken = request.headers['sessionToken']
        # Comprueba que el id pertenece a un usuario existente
        try:
            user = User.objects.get(token=sessionToken)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        # Carga todos los datos en un diccionario
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "token": user.token
        }
        return JsonResponse(user_info, status=200)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)