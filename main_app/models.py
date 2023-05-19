from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    zip_code = models.CharField(max_length=5)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name="group_user_set",
        related_query_name="user",
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name="permission_user_set",
        related_query_name="user",
        help_text='Specific permissions for this user.',
    )

class Portfolio(models.Model):
    user = models.ForeignKey(User, related_name='portfolios', on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=5) # "STOCK" or "CRYPTO"
    ticker = models.CharField(max_length=10)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('user', 'ticker')
    
class Trade(models.Model):
    user = models.ForeignKey(User, related_name='trades', on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=10)  # "Stock" or "Crypto"
    ticker = models.CharField(max_length=10)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    trade_type = models.CharField(max_length=4)  # "BUY" or "SELL"
    timestamp = models.DateTimeField(auto_now_add=True)

class Follower(models.Model):
    user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'followed_user')