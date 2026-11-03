from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login),
    path('eu/', views.eu),

    path('aluno/painel/', views.aluno_painel),

    path('docente/painel/', views.docente_painel),
    path('docente/turmas/<int:pk>/alunos/', views.docente_alunos_turma),
    path('docente/turmas/<int:pk>/notas/', views.docente_salvar_notas),
    path('docente/turmas/<int:pk>/frequencia/', views.docente_registrar_frequencia),
    path('docente/turmas/<int:pk>/plano/', views.docente_plano),

    path('ti/painel/', views.ti_painel),
    path('ti/usuarios/', views.ti_usuarios),
    path('ti/cadastrar/', views.ti_cadastrar),
    path('ti/usuarios/<str:tipo>/<int:pk>/senha/', views.ti_redefinir_senha),

    path('ti/cursos/', views.ti_cursos),
    path('ti/cursos/<int:pk>/', views.ti_curso),
    path('ti/disciplinas/', views.ti_disciplinas),
    path('ti/disciplinas/<int:pk>/', views.ti_disciplina),
    path('ti/disciplinas/<int:pk>/horarios/', views.ti_horario_criar),
    path('ti/horarios/<int:pk>/', views.ti_horario_remover),
    path('ti/disciplinas/<int:pk>/matriculas/', views.ti_matriculas),
    path('ti/matriculas/<int:pk>/', views.ti_matricula_remover),
]
