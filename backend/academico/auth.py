"""Autenticação por token assinado (enviado no header Authorization: Bearer ...)."""
import json
from functools import wraps

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Aluno, Corporativo, Docente

MODELOS = {'aluno': Aluno, 'docente': Docente, 'corporativo': Corporativo}
VALIDADE_TOKEN = 60 * 60 * 12  # 12 horas

_signer = signing.TimestampSigner(salt='acadsystem.token')


def gerar_token(perfil, pk):
    return _signer.sign_object({'p': perfil, 'i': pk})


def usuario_da_requisicao(request):
    """Retorna (perfil, usuario) a partir do token, ou (None, None)."""
    cabecalho = request.headers.get('Authorization', '')
    if not cabecalho.startswith('Bearer '):
        return None, None
    try:
        dados = _signer.unsign_object(cabecalho[7:], max_age=VALIDADE_TOKEN)
        usuario = MODELOS[dados['p']].objects.get(pk=dados['i'])
    except (signing.BadSignature, KeyError, MODELOS['aluno'].DoesNotExist,
            MODELOS['docente'].DoesNotExist, MODELOS['corporativo'].DoesNotExist):
        return None, None
    return dados['p'], usuario


def requer_perfil(*perfis):
    """Protege a view: exige token válido e um dos perfis informados."""
    def decorador(view):
        @csrf_exempt  # a autenticação é por header, não por cookie
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            perfil, usuario = usuario_da_requisicao(request)
            if usuario is None:
                return JsonResponse({'erro': 'Sessão expirada. Faça login novamente.'}, status=401)
            if perfis and perfil not in perfis:
                return JsonResponse({'erro': 'Acesso negado para este perfil.'}, status=403)
            request.perfil = perfil
            request.usuario = usuario
            return view(request, *args, **kwargs)
        return wrapper
    return decorador


def corpo_json(request):
    try:
        dados = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return {}
    return dados if isinstance(dados, dict) else {}
