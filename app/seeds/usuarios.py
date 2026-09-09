from django.contrib.auth import get_user_model

def run():
    Usuario = get_user_model()
    if not Usuario.objects.filter(username="admin").exists():
        Usuario.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
            rol="ADMIN",
            ci="12345678"
        )
        print("✅ Usuario admin creado")
    else:
        print("⚠️ Usuario admin ya existe")
