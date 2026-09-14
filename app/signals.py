from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

@receiver(post_migrate)
def crear_grupos_basicos(sender, **kwargs):
    # Evita ejecutarse en apps ajenas
    if sender.name != "app":
        return
    for nombre in ["admin", "empleado", "residente"]:
        Group.objects.get_or_create(name=nombre)
