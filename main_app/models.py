from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    zip_code = models.CharField(max_length=5)
    funds = models.DecimalField(max_digits=10, decimal_places=2, default=1000.0)
    watchlist = ArrayField(models.CharField(max_length=10), blank=True,default=list)

ASSET_TYPES = [
    ('STOCK', 'Stock'),
    ('CRYPTO', 'Crypto'),
]

TRADE_TYPES = [
    ('BUY', 'Buy'),
    ('SELL', 'Sell'),
]

class Trade(models.Model):
    user = models.ForeignKey(User, related_name='trades', on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)  # "Stock" or "Crypto"
    ticker = models.CharField(max_length=10)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)  # "BUY" or "SELL"
    timestamp = models.DateTimeField(auto_now_add=True)

class Follower(models.Model):
    user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'followed_user')
