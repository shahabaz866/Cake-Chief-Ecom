from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Wallet
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_wallet(sender, instance, **kwargs):
    instance.wallet.save()
