# CarBuy Backend

Este es el backend del proyecto **CarBuy**, una aplicación web para la compra y venta de automóviles. Este backend está construido con Django y proporciona una API RESTful para gestionar usuarios, coches y sus relaciones.

## Tecnologías Utilizadas

- **Python 3**
- **Django 3**
- **Django REST framework**
- **SQLite** (puedes cambiar a otra base de datos si lo necesitas)
- **bcrypt** (para hashing de contraseñas)

## Estructura del Proyecto

- `carbuyrest22app/`: Contiene la aplicación principal de Django.
  - `models.py`: Define los modelos de la base de datos.
  - `views.py`: Contiene la lógica de los endpoints de la API.
  - `urls.py`: Define las rutas de la API.
  - `serializers.py`: Define los serializadores para los modelos.
  - `endpoints.py`: Contiene los endpoints para las operaciones de la API.

## Instalación y Configuración

### Prerrequisitos

- **Python 3.x** y **pip** instalados.

### Pasos de Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/onebeiss/CarBuy-Backend.git
   cd CarBuy-Backend
