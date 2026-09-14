import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")
django.setup()

from app.seeds.usuarios import run

if __name__ == "__main__":
    run()
