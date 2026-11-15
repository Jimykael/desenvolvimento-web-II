from django import forms
from django.contrib import admin
from django.db.models import Count

from . import models


class MatriculaPorDisciplinaInline(admin.TabularInline):
    model = models.Matricula
    fields = ('aluno',)
    autocomplete_fields = ('aluno',)
    extra = 1
    verbose_name = 'aluno matriculado'
    verbose_name_plural = 'alunos matriculados'


class MatriculaPorAlunoInline(admin.TabularInline):
    model = models.Matricula
    fields = ('disciplina', 'n1', 'n2', 'n3')
    autocomplete_fields = ('disciplina',)
    extra = 1
    verbose_name = 'disciplina cursada'
    verbose_name_plural = 'disciplinas cursadas'


class DisciplinaDocenteInline(admin.TabularInline):
    model = models.Disciplina
    fields = ('codigo', 'nome', 'periodo', 'curso')
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = 'disciplinas lecionadas'

    def has_add_permission(self, request, obj=None):
        return False


class HorarioInline(admin.TabularInline):
    model = models.Horario
    fields = ('dia', 'inicio', 'fim')
    extra = 1


class ContaAdminForm(forms.ModelForm):
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=False,
        help_text='Informe ao menos 6 caracteres; em edições, deixe em branco para manter a senha atual.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._senha_atual = self.instance.senha
        self.fields['senha'].required = self.instance._state.adding

    def clean_senha(self):
        senha = self.cleaned_data.get('senha', '')
        if senha and len(senha) < 6:
            raise forms.ValidationError('A senha deve ter no mínimo 6 caracteres.')
        return senha

    def save(self, commit=True):
        pessoa = super().save(commit=False)
        senha = self.cleaned_data['senha']
        if senha:
            pessoa.definir_senha(senha)
        else:
            pessoa.senha = self._senha_atual
        if commit:
            pessoa.save()
            self.save_m2m()
        return pessoa


class AlunoAdminForm(ContaAdminForm):
    class Meta:
        model = models.Aluno
        fields = ('nome', 'email', 'senha', 'matricula', 'curso')


class DocenteAdminForm(ContaAdminForm):
    class Meta:
        model = models.Docente
        fields = ('nome', 'email', 'senha', 'registro', 'departamento')


class CorporativoAdminForm(ContaAdminForm):
    class Meta:
        model = models.Corporativo
        fields = ('nome', 'usuario', 'email', 'senha')


@admin.register(models.Curso)
class CursoAdmin(admin.ModelAdmin):
    search_fields = ('nome',)


@admin.register(models.Docente)
class DocenteAdmin(admin.ModelAdmin):
    form = DocenteAdminForm
    list_display = ('nome', 'email', 'registro', 'departamento')
    search_fields = ('nome', 'email', 'registro')
    list_filter = ('departamento',)
    inlines = [DisciplinaDocenteInline]


@admin.register(models.Aluno)
class AlunoAdmin(admin.ModelAdmin):
    form = AlunoAdminForm
    list_display = ('nome', 'email', 'matricula', 'curso')
    search_fields = ('nome', 'email', 'matricula')
    list_filter = ('curso',)
    list_select_related = ('curso',)
    inlines = [MatriculaPorAlunoInline]


@admin.register(models.Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'docente', 'curso', 'periodo', 'total_alunos')
    list_filter = ('curso', 'docente', 'periodo')
    search_fields = ('codigo', 'nome', 'docente__nome')
    autocomplete_fields = ('docente', 'curso')
    list_select_related = ('docente', 'curso')
    inlines = [HorarioInline, MatriculaPorDisciplinaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_alunos=Count('matriculas'))

    @admin.display(description='Alunos', ordering='_alunos')
    def total_alunos(self, obj):
        return obj._alunos


@admin.register(models.Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'docente', 'dia', 'inicio', 'fim')
    list_filter = ('dia', 'disciplina__curso', 'disciplina__docente')
    search_fields = ('disciplina__codigo', 'disciplina__nome', 'disciplina__docente__nome')
    autocomplete_fields = ('disciplina',)
    list_select_related = ('disciplina', 'disciplina__docente')

    @admin.display(description='Docente', ordering='disciplina__docente__nome')
    def docente(self, obj):
        return obj.disciplina.docente


@admin.register(models.Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'disciplina', 'docente', 'n1', 'n2', 'n3')
    list_filter = ('disciplina__curso', 'disciplina', 'disciplina__docente')
    search_fields = ('aluno__nome', 'aluno__matricula', 'disciplina__codigo', 'disciplina__nome')
    autocomplete_fields = ('aluno', 'disciplina')
    list_select_related = ('aluno', 'disciplina', 'disciplina__docente')

    @admin.display(description='Docente', ordering='disciplina__docente__nome')
    def docente(self, obj):
        return obj.disciplina.docente


@admin.register(models.Corporativo)
class CorporativoAdmin(admin.ModelAdmin):
    form = CorporativoAdminForm
    list_display = ('nome', 'usuario', 'email')
    search_fields = ('nome', 'usuario', 'email')


@admin.register(models.Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'data')
    list_filter = ('disciplina',)
    search_fields = ('disciplina__codigo', 'disciplina__nome')
    autocomplete_fields = ('disciplina',)


@admin.register(models.Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('aula', 'aluno', 'presente')
    list_filter = ('presente', 'aula__disciplina')
    search_fields = ('aluno__nome', 'aluno__matricula')
    autocomplete_fields = ('aula', 'aluno')


