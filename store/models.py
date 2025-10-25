from django.contrib.auth.models import User
from django.db import models



class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.name
    


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order_number = models.IntegerField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100)
    address = models.TextField(null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_number} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name