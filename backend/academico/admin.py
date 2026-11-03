from django.contrib import admin

from . import models


class HorarioInline(admin.TabularInline):
    model = models.Horario
    extra = 1


@admin.register(models.Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'docente', 'curso', 'periodo')
    search_fields = ('codigo', 'nome')
    inlines = [HorarioInline]


@admin.register(models.Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'disciplina', 'n1', 'n2')
    list_filter = ('disciplina',)
    autocomplete_fields = ('aluno',)


@admin.register(models.Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'matricula', 'curso')
    search_fields = ('nome', 'email', 'matricula')
    exclude = ('senha',)  # senhas são definidas pelo portal da TI


@admin.register(models.Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'registro', 'departamento')
    search_fields = ('nome', 'email', 'registro')
    exclude = ('senha',)


admin.site.register(models.Curso)
admin.site.register(models.Corporativo)
admin.site.register(models.Aula)
admin.site.register(models.Presenca)
