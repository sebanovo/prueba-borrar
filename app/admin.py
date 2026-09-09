from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from app.models.usuario import Usuario
from app.models.residencia import Apartamento, Residente  # si ya creaste estos modelos
from app.forms import UsuarioCreationForm, UsuarioChangeForm

# Inline para ver estancias (historial de ocupación) en el detalle del Usuario:
class ResidenteInline(admin.TabularInline):
    model = Residente
    extra = 0
    autocomplete_fields = ("apartamento",)
    readonly_fields = ("fecha_ingreso", "fecha_salida")
    can_delete = False

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Usa los formularios custom
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario

    # Qué columnas ver en la lista
    list_display = ("email", "username", "first_name", "last_name", "ci", "rol", "is_staff", "is_active", "date_joined")
    list_filter = ("rol", "is_staff", "is_active")

    # Búsqueda
    search_fields = ("email", "username", "first_name", "last_name", "ci")
    ordering = ("email",)  # como tu login es por email, suele ser cómodo

    # Campos de solo lectura
    readonly_fields = ("last_login", "date_joined")

    # Secciones del formulario de edición (DETALLE)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email", "ci", "telefono", "foto", "fecha_nacimiento")}),
        ("Roles y permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    # Secciones del formulario de creación (ALTA)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "username",
                "first_name", "last_name",
                "ci", "telefono", "fecha_nacimiento", "foto",
                "rol", "is_staff", "is_active",
                "password1", "password2",
            ),
        }),
    )

    # Inline para ver estancias del usuario (si ya tienes Residente)
    inlines = [ResidenteInline]


# Admin para Apartamento y Residente (opcional pero útil)
@admin.register(Apartamento)
class ApartamentoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "bloque", "piso", "activo")
    search_fields = ("codigo", "bloque")
    list_filter = ("activo",)
    ordering = ("codigo",)

class ResidenteUsuarioInline(admin.TabularInline):
    model = Residente
    extra = 0
    autocomplete_fields = ("usuario",)
    readonly_fields = ("fecha_ingreso", "fecha_salida")
    can_delete = False

@admin.register(Residente)
class ResidenteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "apartamento", "fecha_ingreso", "fecha_salida")
    list_filter = ("apartamento", "fecha_salida")
    search_fields = ("usuario__email", "usuario__ci", "apartamento__codigo")
    autocomplete_fields = ("usuario", "apartamento")
