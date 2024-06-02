from django.db import models

class User(models.Model):
    email = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=120)
    encrypted_password = models.CharField(max_length=120)
    birthdate = models.DateField(auto_now_add=False)
    phone = models.CharField(max_length=15)
    token = models.CharField(unique=True, null=True, max_length=50)

    def to_jsonAccount(self):
        return {
            "email": self.email
        }

class Car(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image_url = models.URLField(default='https://shorturl.at/YJLnZ')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class FavouriteCar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)