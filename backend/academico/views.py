import re
from datetime import date, time
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth import corpo_json, gerar_token, requer_perfil
from .models import (Aluno, Aula, Corporativo, Curso, Disciplina, Docente,
                     Horario, Matricula, Presenca)

REGEX_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}')
FREQUENCIA_MINIMA = 75
MIN_AULAS_AVALIACAO = 4


def erro(mensagem, status=400):
    return JsonResponse({'erro': mensagem}, status=status)


def detalhe_usuario(perfil, u):
    """Texto exibido sob o nome na topbar."""
    if perfil == 'aluno':
        curso = u.curso.nome if u.curso else 'Sem curso'
        return f'{curso} · Matrícula {u.matricula}'
    if perfil == 'docente':
        return f'{u.departamento or "Docente"} · Registro {u.registro}'
    return f'Equipe de Tecnologia · {u.usuario}'


# ---------------------------------------------------------------- LOGIN

@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    dados = corpo_json(request)
    perfil = dados.get('perfil')
    identificador = str(dados.get('identificador', '')).strip()
    senha = str(dados.get('senha', ''))

    if perfil not in ('aluno', 'docente', 'corporativo'):
        return erro('Perfil inválido.')
    if not identificador or not senha:
        return erro('Por favor, preencha todos os campos.')
    if perfil == 'aluno' and '@' not in identificador:
        return erro('O acesso do aluno é feito pelo e-mail institucional.')

    if perfil == 'aluno':
        usuario = Aluno.objects.filter(email__iexact=identificador).first()
    elif perfil == 'docente':
        usuario = Docente.objects.filter(
            Q(email__iexact=identificador) | Q(registro=identificador)).first()
    else:
        usuario = Corporativo.objects.filter(
            Q(usuario__iexact=identificador) | Q(email__iexact=identificador)).first()

    if usuario is None or not usuario.conferir_senha(senha):
        return erro('Login ou senha incorretos. Se ainda não tem acesso, procure o setor de TI.', 401)

    return JsonResponse({
        'token': gerar_token(perfil, usuario.pk),
        'perfil': perfil,
        'nome': usuario.nome,
        'detalhe': detalhe_usuario(perfil, usuario),
    })


@requer_perfil()
def eu(request):
    return JsonResponse({
        'perfil': request.perfil,
        'nome': request.usuario.nome,
        'detalhe': detalhe_usuario(request.perfil, request.usuario),
    })


# ---------------------------------------------------------------- ALUNO

def _num(valor):
    return None if valor is None else float(valor)


def _frequencia(disciplina, aluno):
    """Percentual de presença do aluno na disciplina (None se ainda não há aulas)."""
    total = disciplina.aulas.count()
    if total == 0:
        return None
    presentes = Presenca.objects.filter(aula__disciplina=disciplina, aluno=aluno, presente=True).count()
    return round(presentes * 100 / total, 1)


def _media(m):
    valores = [v for v in (m.n1, m.n2) if v is not None]
    if not valores:
        return None
    return round(float(sum(valores) / len(valores)), 1)


def _situacao(m, freq):
    # Com poucas aulas registradas, uma falta distorce muito o percentual:
    # só reprova por falta a partir de MIN_AULAS_AVALIACAO aulas; antes disso, apenas alerta.
    if freq is not None and freq < FREQUENCIA_MINIMA:
        if m.disciplina.aulas.count() >= MIN_AULAS_AVALIACAO:
            return {'rotulo': 'Reprovado por falta', 'classe': 'pill-red'}
        return {'rotulo': 'Atenção', 'classe': 'pill-amber'}
    media = _media(m)
    if m.n1 is not None and m.n2 is not None:
        if media >= 6:
            return {'rotulo': 'Aprovado', 'classe': 'pill-green'}
        return {'rotulo': 'Reprovado', 'classe': 'pill-red'}
    if media is not None and media < 6:
        return {'rotulo': 'Atenção', 'classe': 'pill-amber'}
    if freq is not None and freq < 85:
        return {'rotulo': 'Atenção', 'classe': 'pill-amber'}
    return {'rotulo': 'Cursando', 'classe': 'pill-green'}


@requer_perfil('aluno')
def aluno_painel(request):
    aluno = request.usuario
    matriculas = list(aluno.matriculas.select_related('disciplina').order_by('disciplina__nome'))

    boletim, frequencias, medias = [], [], []
    presencas_total = aulas_total = carga = 0
    for m in matriculas:
        d = m.disciplina
        freq = _frequencia(d, aluno)
        media = _media(m)
        if media is not None:
            medias.append(media)
        carga += d.carga_horaria
        n_aulas = d.aulas.count()
        aulas_total += n_aulas
        if n_aulas:
            presencas_total += Presenca.objects.filter(aula__disciplina=d, aluno=aluno, presente=True).count()
        boletim.append({
            'disciplina': d.nome, 'codigo': d.codigo,
            'n1': _num(m.n1), 'n2': _num(m.n2), 'media': media,
            'frequencia': freq, 'situacao': _situacao(m, freq),
        })
        frequencias.append({'disciplina': d.nome, 'percentual': freq})

    # Grade de horários: lista plana; o frontend monta a tabela
    horarios = []
    for m in matriculas:
        for h in m.disciplina.horarios.all():
            horarios.append({
                'dia': h.dia, 'inicio': h.inicio.strftime('%H:%M'), 'fim': h.fim.strftime('%H:%M'),
                'disciplina': m.disciplina.nome,
            })

    return JsonResponse({
        'resumo': {
            'cr': round(sum(medias) / len(medias), 1) if medias else None,
            'frequencia_geral': round(presencas_total * 100 / aulas_total, 1) if aulas_total else None,
            'disciplinas': len(matriculas),
            'carga_horaria': carga,
            'rematricula': 'Confirmada' if matriculas else 'Sem matrícula',
        },
        'boletim': boletim,
        'frequencias': frequencias,
        'horarios': horarios,
    })


# ---------------------------------------------------------------- DOCENTE

def _disciplina_do_docente(request, pk):
    return Disciplina.objects.filter(pk=pk, docente=request.usuario).first()


@requer_perfil('docente')
def docente_painel(request):
    disciplinas = list(request.usuario.disciplinas.prefetch_related('horarios', 'matriculas'))
    nomes_dia = dict(Horario.DIAS)

    turmas, total_alunos, pendentes, aulas = [], 0, 0, 0
    for d in disciplinas:
        n_alunos = d.matriculas.count()
        total_alunos += n_alunos
        pendentes += d.matriculas.filter(Q(n1__isnull=True) | Q(n2__isnull=True)).count()
        aulas += d.aulas.count()
        dias = ' / '.join(nomes_dia[h.dia][:3] for h in d.horarios.all())
        horas = ''
        if d.horarios.all():
            h0 = d.horarios.all()[0]
            horas = f'{h0.inicio:%H:%M} às {h0.fim:%H:%M}'
        turmas.append({
            'id': d.id, 'nome': d.nome, 'codigo': d.codigo,
            'curso': d.curso.nome if d.curso else 'Sem curso',
            'alunos': n_alunos, 'dias': dias, 'horario': horas,
        })

    return JsonResponse({
        'resumo': {'turmas': len(disciplinas), 'alunos': total_alunos,
                   'aulas_lancadas': aulas, 'notas_pendentes': pendentes},
        'turmas': turmas,
    })


@requer_perfil('docente')
def docente_alunos_turma(request, pk):
    d = _disciplina_do_docente(request, pk)
    if d is None:
        return erro('Turma não encontrada.', 404)
    alunos = [{
        'id': m.aluno_id, 'matricula': m.aluno.matricula, 'nome': m.aluno.nome,
        'n1': _num(m.n1), 'n2': _num(m.n2),
    } for m in d.matriculas.select_related('aluno').order_by('aluno__nome')]
    return JsonResponse({'turma': {'id': d.id, 'nome': d.nome, 'codigo': d.codigo}, 'alunos': alunos})


def _parse_nota(valor):
    if valor in (None, ''):
        return None
    try:
        nota = Decimal(str(valor).replace(',', '.'))
    except InvalidOperation:
        raise ValueError('Nota inválida.')
    if nota < 0 or nota > 10:
        raise ValueError('As notas devem estar entre 0 e 10.')
    return nota


@requer_perfil('docente')
@require_http_methods(['POST'])
def docente_salvar_notas(request, pk):
    d = _disciplina_do_docente(request, pk)
    if d is None:
        return erro('Turma não encontrada.', 404)
    itens = corpo_json(request).get('notas')
    if not isinstance(itens, list):
        return erro('Dados inválidos.')
    try:
        with transaction.atomic():
            for item in itens:
                m = Matricula.objects.filter(disciplina=d, aluno_id=item.get('aluno_id')).first()
                if m is None:
                    raise ValueError('Aluno não pertence a esta turma.')
                m.n1 = _parse_nota(item.get('n1'))
                m.n2 = _parse_nota(item.get('n2'))
                m.save(update_fields=['n1', 'n2'])
    except ValueError as e:
        return erro(str(e))
    return JsonResponse({'ok': True})


@requer_perfil('docente')
@require_http_methods(['POST'])
def docente_registrar_frequencia(request, pk):
    d = _disciplina_do_docente(request, pk)
    if d is None:
        return erro('Turma não encontrada.', 404)
    dados = corpo_json(request)
    try:
        data = date.fromisoformat(str(dados.get('data', '')))
    except ValueError:
        return erro('Data inválida.')
    if data > date.today():
        return erro('Não é possível registrar frequência em data futura.')
    presencas = dados.get('presencas')
    if not isinstance(presencas, list):
        return erro('Dados inválidos.')

    matriculados = set(d.matriculas.values_list('aluno_id', flat=True))
    with transaction.atomic():
        aula, _ = Aula.objects.get_or_create(disciplina=d, data=data)
        for item in presencas:
            aluno_id = item.get('aluno_id')
            if aluno_id not in matriculados:
                continue
            Presenca.objects.update_or_create(
                aula=aula, aluno_id=aluno_id, defaults={'presente': bool(item.get('presente'))})
    presentes = aula.presencas.filter(presente=True).count()
    return JsonResponse({'ok': True, 'presentes': presentes, 'total': len(matriculados)})


@requer_perfil('docente')
@require_http_methods(['GET', 'PUT'])
def docente_plano(request, pk):
    d = _disciplina_do_docente(request, pk)
    if d is None:
        return erro('Turma não encontrada.', 404)
    if request.method == 'PUT':
        dados = corpo_json(request)
        try:
            carga = int(str(dados.get('carga_horaria', d.carga_horaria)).lower().replace('h', '').strip())
        except ValueError:
            return erro('Carga horária inválida.')
        if carga <= 0:
            return erro('Carga horária inválida.')
        d.ementa = str(dados.get('ementa', ''))[:5000]
        d.bibliografia = str(dados.get('bibliografia', ''))[:255]
        d.carga_horaria = carga
        d.save()
    return JsonResponse({'codigo': d.codigo, 'nome': d.nome, 'ementa': d.ementa,
                         'carga_horaria': d.carga_horaria, 'bibliografia': d.bibliografia})


# ---------------------------------------------------------------- TI

@requer_perfil('corporativo')
def ti_painel(request):
    return JsonResponse({
        'alunos': Aluno.objects.count(),
        'docentes': Docente.objects.count(),
        'disciplinas': Disciplina.objects.count(),
        'cursos': list(Curso.objects.values('id', 'nome')),
    })


@requer_perfil('corporativo')
def ti_usuarios(request):
    usuarios = [{'tipo': 'Aluno', 'id': a.id, 'nome': a.nome, 'email': a.email, 'identificador': a.matricula}
                for a in Aluno.objects.all()]
    usuarios += [{'tipo': 'Docente', 'id': p.id, 'nome': p.nome, 'email': p.email, 'identificador': p.registro}
                 for p in Docente.objects.all()]
    usuarios.sort(key=lambda u: u['nome'].lower())
    return JsonResponse({'usuarios': usuarios})


@requer_perfil('corporativo')
@require_http_methods(['POST'])
def ti_cadastrar(request):
    dados = corpo_json(request)
    tipo = dados.get('tipo')
    nome = str(dados.get('nome', '')).strip()
    email = str(dados.get('email', '')).strip().lower()
    identificador = str(dados.get('identificador', '')).strip()
    senha = str(dados.get('senha', ''))

    if tipo not in ('Aluno', 'Docente'):
        return erro('Tipo de cadastro inválido.')
    if not (nome and email and identificador and senha):
        return erro('Preencha todos os campos!')
    if not REGEX_EMAIL.fullmatch(email):
        return erro('Digite um e-mail válido. Ex: nome.sobrenome@uneb.br')
    if len(senha) < 6:
        return erro('A senha deve ter no mínimo 6 caracteres!')

    if tipo == 'Aluno':
        modelo, campo_id, rotulo_id = Aluno, 'matricula', 'essa matrícula'
    else:
        modelo, campo_id, rotulo_id = Docente, 'registro', 'esse número de registro'

    if modelo.objects.filter(email__iexact=email).exists():
        return erro('Este e-mail já está cadastrado!')
    if modelo.objects.filter(**{campo_id: identificador}).exists():
        return erro(f'Já existe um cadastro com {rotulo_id}!')

    pessoa = modelo(nome=nome, email=email, **{campo_id: identificador})
    if tipo == 'Aluno':
        curso_id = dados.get('curso_id')
        if curso_id:
            pessoa.curso = Curso.objects.filter(pk=curso_id).first()
    else:
        pessoa.departamento = str(dados.get('departamento', '')).strip()[:120]
    pessoa.definir_senha(senha)
    pessoa.save()
    return JsonResponse({'ok': True, 'usuario': {
        'tipo': tipo, 'id': pessoa.id, 'nome': pessoa.nome, 'email': pessoa.email,
        'identificador': identificador}}, status=201)


@requer_perfil('corporativo')
@require_http_methods(['POST'])
def ti_redefinir_senha(request, tipo, pk):
    modelo = {'Aluno': Aluno, 'Docente': Docente}.get(tipo)
    if modelo is None:
        return erro('Tipo inválido.')
    pessoa = modelo.objects.filter(pk=pk).first()
    if pessoa is None:
        return erro('Usuário não encontrado.', 404)
    senha = str(corpo_json(request).get('senha', ''))
    if len(senha) < 6:
        return erro('A senha deve ter no mínimo 6 caracteres!')
    pessoa.definir_senha(senha)
    pessoa.save(update_fields=['senha'])
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------- TI: ACADÊMICO
# Cursos, disciplinas, horários e matrículas

def _texto(dados, campo, maximo):
    return str(dados.get(campo, '')).strip()[:maximo]


@requer_perfil('corporativo')
@require_http_methods(['GET', 'POST'])
def ti_cursos(request):
    if request.method == 'POST':
        nome = _texto(corpo_json(request), 'nome', 120)
        if not nome:
            return erro('Informe o nome do curso.')
        if Curso.objects.filter(nome__iexact=nome).exists():
            return erro('Já existe um curso com esse nome.')
        Curso.objects.create(nome=nome)
    cursos = [{'id': c.id, 'nome': c.nome, 'alunos': c.alunos.count(), 'disciplinas': c.disciplinas.count()}
              for c in Curso.objects.all()]
    return JsonResponse({'cursos': cursos})


@requer_perfil('corporativo')
@require_http_methods(['PUT', 'DELETE'])
def ti_curso(request, pk):
    curso = Curso.objects.filter(pk=pk).first()
    if curso is None:
        return erro('Curso não encontrado.', 404)
    if request.method == 'DELETE':
        curso.delete()  # alunos e disciplinas ficam "sem curso"
        return JsonResponse({'ok': True})
    nome = _texto(corpo_json(request), 'nome', 120)
    if not nome:
        return erro('Informe o nome do curso.')
    if Curso.objects.filter(nome__iexact=nome).exclude(pk=pk).exists():
        return erro('Já existe um curso com esse nome.')
    curso.nome = nome
    curso.save()
    return JsonResponse({'ok': True})


def _disciplina_json(d):
    return {
        'id': d.id, 'codigo': d.codigo, 'nome': d.nome, 'carga_horaria': d.carga_horaria,
        'periodo': d.periodo,
        'curso_id': d.curso_id, 'curso': d.curso.nome if d.curso else '',
        'docente_id': d.docente_id, 'docente': d.docente.nome if d.docente else '',
        'alunos': d.matriculas.count(),
        'horarios': [{'id': h.id, 'dia': h.dia, 'dia_nome': h.get_dia_display(),
                      'inicio': h.inicio.strftime('%H:%M'), 'fim': h.fim.strftime('%H:%M')}
                     for h in d.horarios.all()],
    }


def _validar_disciplina(dados, pk=None):
    """Retorna (campos, erro). Campos prontos para gravar no model."""
    codigo = _texto(dados, 'codigo', 20).upper()
    nome = _texto(dados, 'nome', 150)
    periodo = _texto(dados, 'periodo', 10) or '2026.1'
    if not codigo or not nome:
        return None, 'Informe o código e o nome da disciplina.'
    try:
        carga = int(dados.get('carga_horaria') or 68)
    except (TypeError, ValueError):
        return None, 'Carga horária inválida.'
    if carga <= 0:
        return None, 'Carga horária inválida.'
    if Disciplina.objects.filter(codigo__iexact=codigo).exclude(pk=pk).exists():
        return None, 'Já existe uma disciplina com esse código.'

    curso = docente = None
    if dados.get('curso_id'):
        curso = Curso.objects.filter(pk=dados['curso_id']).first()
        if curso is None:
            return None, 'Curso não encontrado.'
    if dados.get('docente_id'):
        docente = Docente.objects.filter(pk=dados['docente_id']).first()
        if docente is None:
            return None, 'Docente não encontrado.'
    return {'codigo': codigo, 'nome': nome, 'periodo': periodo, 'carga_horaria': carga,
            'curso': curso, 'docente': docente}, None


@requer_perfil('corporativo')
@require_http_methods(['GET', 'POST'])
def ti_disciplinas(request):
    if request.method == 'POST':
        campos, msg = _validar_disciplina(corpo_json(request))
        if msg:
            return erro(msg)
        Disciplina.objects.create(**campos)
    qs = Disciplina.objects.select_related('curso', 'docente').prefetch_related('horarios', 'matriculas')
    return JsonResponse({
        'disciplinas': [_disciplina_json(d) for d in qs],
        'docentes': [{'id': p.id, 'nome': p.nome} for p in Docente.objects.all()],
        'cursos': [{'id': c.id, 'nome': c.nome} for c in Curso.objects.all()],
    })


@requer_perfil('corporativo')
@require_http_methods(['PUT', 'DELETE'])
def ti_disciplina(request, pk):
    d = Disciplina.objects.filter(pk=pk).first()
    if d is None:
        return erro('Disciplina não encontrada.', 404)
    if request.method == 'DELETE':
        d.delete()  # remove também horários, matrículas, aulas e presenças
        return JsonResponse({'ok': True})
    campos, msg = _validar_disciplina(corpo_json(request), pk)
    if msg:
        return erro(msg)
    for chave, valor in campos.items():
        setattr(d, chave, valor)
    d.save()
    return JsonResponse({'ok': True})


@requer_perfil('corporativo')
@require_http_methods(['POST'])
def ti_horario_criar(request, pk):
    d = Disciplina.objects.filter(pk=pk).first()
    if d is None:
        return erro('Disciplina não encontrada.', 404)
    dados = corpo_json(request)
    try:
        dia = int(dados.get('dia'))
        inicio = time.fromisoformat(str(dados.get('inicio', '')))
        fim = time.fromisoformat(str(dados.get('fim', '')))
    except (TypeError, ValueError):
        return erro('Informe dia, hora inicial e hora final válidos.')
    if dia not in dict(Horario.DIAS):
        return erro('Dia da semana inválido.')
    if inicio >= fim:
        return erro('A hora final deve ser maior que a inicial.')

    # Conflito com a própria disciplina ou com outra do mesmo docente
    conflitos = Horario.objects.filter(dia=dia, inicio__lt=fim, fim__gt=inicio)
    filtro = Q(disciplina=d)
    if d.docente_id:
        filtro |= Q(disciplina__docente_id=d.docente_id)
    outro = conflitos.filter(filtro).select_related('disciplina').first()
    if outro:
        return erro(f'Conflito de horário com {outro.disciplina.codigo} '
                    f'({outro.inicio:%H:%M}–{outro.fim:%H:%M}).')
    Horario.objects.create(disciplina=d, dia=dia, inicio=inicio, fim=fim)
    return JsonResponse({'ok': True}, status=201)


@requer_perfil('corporativo')
@require_http_methods(['DELETE'])
def ti_horario_remover(request, pk):
    deletados, _ = Horario.objects.filter(pk=pk).delete()
    if not deletados:
        return erro('Horário não encontrado.', 404)
    return JsonResponse({'ok': True})


@requer_perfil('corporativo')
@require_http_methods(['GET', 'POST'])
def ti_matriculas(request, pk):
    d = Disciplina.objects.filter(pk=pk).first()
    if d is None:
        return erro('Disciplina não encontrada.', 404)
    if request.method == 'POST':
        aluno = Aluno.objects.filter(pk=corpo_json(request).get('aluno_id')).first()
        if aluno is None:
            return erro('Aluno não encontrado.')
        _, criada = Matricula.objects.get_or_create(aluno=aluno, disciplina=d)
        if not criada:
            return erro('Este aluno já está matriculado na disciplina.')
    matriculados = list(d.matriculas.select_related('aluno').order_by('aluno__nome'))
    ids = {m.aluno_id for m in matriculados}
    return JsonResponse({
        'matriculas': [{'id': m.id, 'aluno': m.aluno.nome, 'matricula': m.aluno.matricula}
                       for m in matriculados],
        'disponiveis': [{'id': a.id, 'nome': a.nome, 'matricula': a.matricula}
                        for a in Aluno.objects.exclude(pk__in=ids)],
    })


@requer_perfil('corporativo')
@require_http_methods(['DELETE'])
def ti_matricula_remover(request, pk):
    deletados, _ = Matricula.objects.filter(pk=pk).delete()
    if not deletados:
        return erro('Matrícula não encontrada.', 404)
    return JsonResponse({'ok': True})
