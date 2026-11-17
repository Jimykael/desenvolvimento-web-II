"""Testes automatizados do backend AcadSystem.

Coloque este arquivo em backend/, ao lado de manage.py.
Execute, com as dependências do projeto instaladas: python test_sistema.py
A execução direta usa SQLite em memória e não acessa o banco configurado.
Também pode ser descoberto pelo runner normal do Django (nesse caso, usa
as configurações de teste fornecidas ao runner).
"""
import os
import sys
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
    from django.conf import settings
    # Antes de django.setup(): nenhuma conexão com PostgreSQL é inicializada.
    settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:',
    }}
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    import django
    django.setup()

from django.core.exceptions import ValidationError
from django.test import TestCase
from academico.auth import gerar_token, VALIDADE_TOKEN
from academico.models import (
    Aluno, Aula, Corporativo, Curso, Disciplina, Docente, Horario,
    Matricula, Presenca,
)
from academico.views import _media, _situacao


class SistemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.curso = Curso.objects.create(nome='Engenharia')
        cls.aluno = Aluno(nome='Ana', email='ana@example.com', matricula='A01', curso=cls.curso)
        cls.docente = Docente(nome='Carlos', email='carlos@example.com', registro='D01')
        cls.admin = Corporativo(nome='TI', email='ti@example.com', usuario='admin')
        for conta in (cls.aluno, cls.docente, cls.admin):
            conta.definir_senha('SenhaTeste123!')
            conta.save()
        cls.disciplina = Disciplina.objects.create(
            codigo='WEB2', nome='Web II', curso=cls.curso, docente=cls.docente,
        )
        cls.matricula = Matricula.objects.create(aluno=cls.aluno, disciplina=cls.disciplina)

    def autenticar(self, perfil='corporativo', conta=None):
        contas = {'corporativo': self.admin, 'aluno': self.aluno, 'docente': self.docente}
        token = gerar_token(perfil, (conta or contas[perfil]).pk)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    def enviar(self, url, dados, metodo='post'):
        return getattr(self.client, metodo)(url, dados, content_type='application/json')

    def url_turma(self, recurso):
        return f'/api/docente/turmas/{self.disciplina.pk}/{recurso}/'

    def registrar_aulas(self, quantidade, presentes):
        for i in range(quantidade):
            aula = Aula.objects.create(disciplina=self.disciplina, data=date.today() - timedelta(days=i))
            Presenca.objects.create(aula=aula, aluno=self.aluno, presente=i < presentes)

    def test_senhas_armazenadas_com_hash(self):
        for conta in (self.aluno, self.docente, self.admin):
            with self.subTest(conta=type(conta).__name__):
                self.assertNotEqual(conta.senha, 'SenhaTeste123!')
                self.assertTrue(conta.conferir_senha('SenhaTeste123!'))
                self.assertFalse(conta.conferir_senha('errada'))

    def test_login_dos_tres_perfis(self):
        for perfil, conta in [('aluno', self.aluno), ('docente', self.docente), ('corporativo', self.admin)]:
            with self.subTest(perfil=perfil):
                resposta = self.enviar('/api/login/', {
                    'email': f' {conta.email.upper()} ', 'senha': 'SenhaTeste123!',
                })
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()['perfil'], perfil)
                self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + resposta.json()['token']
                self.assertEqual(self.client.get('/api/eu/').json()['nome'], conta.nome)

    def test_login_recusa_senha_incorreta(self):
        resposta = self.enviar('/api/login/', {'email': self.aluno.email, 'senha': 'errada'})
        self.assertEqual(resposta.status_code, 401)
        self.assertNotIn('token', resposta.json())

    def test_login_recusa_campos_ausentes_e_json_invalido(self):
        for dados in ({}, {'email': self.aluno.email}, {'senha': 'abc'}, []):
            with self.subTest(dados=dados):
                self.assertEqual(self.enviar('/api/login/', dados).status_code, 400)
        self.assertEqual(self.client.post('/api/login/', '{', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get('/api/login/').status_code, 405)

    def test_rotas_exigem_autenticacao(self):
        for url in ('/api/eu/', '/api/aluno/painel/', '/api/docente/painel/', '/api/ti/painel/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_token_adulterado_expirado_e_usuario_excluido(self):
        token = gerar_token('aluno', self.aluno.pk)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}x'
        self.assertEqual(self.client.get('/api/eu/').status_code, 401)
        with patch('django.core.signing.time.time', return_value=1000000000):
            antigo = gerar_token('aluno', self.aluno.pk)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {antigo}'
        with patch('django.core.signing.time.time', return_value=1000000000 + VALIDADE_TOKEN + 1):
            self.assertEqual(self.client.get('/api/eu/').status_code, 401)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        self.aluno.delete()
        self.assertEqual(self.client.get('/api/eu/').status_code, 401)

    def test_perfis_nao_acessam_portais_alheios(self):
        portais = {'aluno': '/api/aluno/painel/', 'docente': '/api/docente/painel/', 'corporativo': '/api/ti/painel/'}
        for perfil in portais:
            self.autenticar(perfil)
            for destino, url in portais.items():
                with self.subTest(perfil=perfil, destino=destino):
                    self.assertEqual(self.client.get(url).status_code, 200 if perfil == destino else 403)

    def test_painel_sem_notas_ou_aulas(self):
        self.autenticar('aluno')
        dados = self.client.get('/api/aluno/painel/').json()
        self.assertIsNone(dados['resumo']['cr'])
        self.assertIsNone(dados['resumo']['frequencia_geral'])
        self.assertEqual(dados['resumo']['disciplinas'], 1)
        self.assertEqual(dados['boletim'][0]['situacao']['rotulo'], 'Cursando')

    def test_painel_calcula_notas_e_frequencia(self):
        self.matricula.n1, self.matricula.n2, self.matricula.n3 = 6, 7, 8
        self.matricula.save()
        self.registrar_aulas(4, 3)
        self.autenticar('aluno')
        dados = self.client.get('/api/aluno/painel/').json()
        self.assertEqual(dados['resumo']['cr'], 7)
        self.assertEqual(dados['resumo']['frequencia_geral'], 75)
        self.assertEqual(dados['boletim'][0]['total'], 21)
        self.assertEqual(dados['boletim'][0]['situacao']['rotulo'], 'Aprovado')

    def test_media_ignora_notas_ausentes_mas_inclui_zero(self):
        self.matricula.n1, self.matricula.n2 = Decimal('0'), Decimal('8')
        self.assertEqual(_media(self.matricula), 4)

    def test_limite_aprovacao_e_notas_pendentes(self):
        for notas, esperado in [((7, 7, 7), 'Aprovado'), ((7, 7, 6), 'Reprovado'), ((8, 8, None), 'Cursando'), ((0, None, None), 'Atenção')]:
            with self.subTest(notas=notas):
                self.matricula.n1, self.matricula.n2, self.matricula.n3 = notas
                self.assertEqual(_situacao(self.matricula, 100)['rotulo'], esperado)

    def test_faltas_so_reprovam_a_partir_de_quatro_aulas(self):
        self.registrar_aulas(3, 0)
        self.assertEqual(_situacao(self.matricula, 0)['rotulo'], 'Atenção')
        Aula.objects.create(disciplina=self.disciplina, data=date.today() - timedelta(days=3))
        self.matricula.n1 = self.matricula.n2 = self.matricula.n3 = 10
        self.assertEqual(_situacao(self.matricula, 0)['rotulo'], 'Reprovado por falta')
        self.assertEqual(_situacao(self.matricula, 75)['rotulo'], 'Aprovado')

    def test_docente_salva_notas_com_virgula_zero_e_nulo(self):
        self.autenticar('docente')
        resposta = self.enviar(self.url_turma('notas'), {'notas': [
            {'aluno_id': self.aluno.pk, 'n1': '7,5', 'n2': 0, 'n3': None},
        ]})
        self.assertEqual(resposta.status_code, 200)
        self.matricula.refresh_from_db()
        self.assertEqual(self.matricula.n1, Decimal('7.50'))
        self.assertEqual(self.matricula.n2, 0)
        self.assertIsNone(self.matricula.n3)

    def test_notas_invalidas_nao_sao_salvas(self):
        self.autenticar('docente')
        for nota in (-1, 11, 'abc'):
            with self.subTest(nota=nota):
                resposta = self.enviar(self.url_turma('notas'), {'notas': [{'aluno_id': self.aluno.pk, 'n1': nota}]})
                self.assertEqual(resposta.status_code, 400)
                self.matricula.refresh_from_db()
                self.assertIsNone(self.matricula.n1)

    def test_lote_de_notas_invalido_desfaz_alteracoes_anteriores(self):
        self.autenticar('docente')
        resposta = self.enviar(self.url_turma('notas'), {'notas': [
            {'aluno_id': self.aluno.pk, 'n1': 9}, {'aluno_id': 999999, 'n1': 8},
        ]})
        self.assertEqual(resposta.status_code, 400)
        self.matricula.refresh_from_db()
        self.assertIsNone(self.matricula.n1)

    def test_docente_nao_acessa_turma_de_outro(self):
        outro = Docente.objects.create(nome='Outro', email='outro@example.com', registro='D02', senha='inutilizada')
        self.autenticar('docente', outro)
        self.assertEqual(self.client.get(self.url_turma('alunos')).status_code, 404)
        self.assertEqual(self.enviar(self.url_turma('notas'), {'notas': []}).status_code, 404)
        self.assertEqual(self.enviar(self.url_turma('frequencia'), {}).status_code, 404)
        self.assertEqual(self.client.get(self.url_turma('plano')).status_code, 404)

    def test_frequencia_atualiza_sem_duplicar(self):
        self.autenticar('docente')
        for presente in (True, False):
            resposta = self.enviar(self.url_turma('frequencia'), {
                'data': date.today().isoformat(),
                'presencas': [{'aluno_id': self.aluno.pk, 'presente': presente}],
            })
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json()['presentes'], int(presente))
        self.assertEqual(Aula.objects.count(), 1)
        self.assertEqual(Presenca.objects.count(), 1)
        self.assertFalse(Presenca.objects.get().presente)

    def test_frequencia_recusa_data_invalida_ou_futura(self):
        self.autenticar('docente')
        for data in ('invalida', (date.today() + timedelta(days=1)).isoformat()):
            with self.subTest(data=data):
                self.assertEqual(self.enviar(self.url_turma('frequencia'), {'data': data, 'presencas': []}).status_code, 400)
        self.assertFalse(Aula.objects.exists())

    def test_plano_de_ensino_persiste_alteracoes(self):
        self.autenticar('docente')
        resposta = self.enviar(self.url_turma('plano'), {'carga_horaria': '80h', 'ementa': 'APIs', 'bibliografia': 'Livro'}, 'put')
        self.assertEqual(resposta.status_code, 200)
        self.disciplina.refresh_from_db()
        self.assertEqual(self.disciplina.carga_horaria, 80)
        self.assertEqual(self.client.get(self.url_turma('plano')).json()['ementa'], 'APIs')
        self.assertEqual(self.enviar(self.url_turma('plano'), {'carga_horaria': -1}, 'put').status_code, 400)

    def test_curso_criacao_duplicidade_e_edicao(self):
        self.autenticar()
        self.assertEqual(self.enviar('/api/ti/cursos/', {'nome': 'Computação'}).status_code, 200)
        curso = Curso.objects.get(nome='Computação')
        self.assertEqual(self.enviar('/api/ti/cursos/', {'nome': 'computação'}).status_code, 400)
        self.assertEqual(self.enviar(f'/api/ti/cursos/{curso.pk}/', {'nome': 'Sistemas'}, 'put').status_code, 200)
        curso.refresh_from_db()
        self.assertEqual(curso.nome, 'Sistemas')

    def test_excluir_curso_preserva_alunos_e_disciplinas(self):
        self.autenticar()
        self.assertEqual(self.client.delete(f'/api/ti/cursos/{self.curso.pk}/').status_code, 200)
        self.aluno.refresh_from_db()
        self.disciplina.refresh_from_db()
        self.assertIsNone(self.aluno.curso_id)
        self.assertIsNone(self.disciplina.curso_id)

    def test_matricula_nao_pode_ser_duplicada_e_pode_ser_removida(self):
        self.autenticar()
        url = f'/api/ti/disciplinas/{self.disciplina.pk}/matriculas/'
        self.assertEqual(self.enviar(url, {'aluno_id': self.aluno.pk}).status_code, 400)
        self.assertEqual(Matricula.objects.count(), 1)
        self.assertEqual(self.client.delete(f'/api/ti/matriculas/{self.matricula.pk}/').status_code, 200)
        self.assertEqual(self.enviar(url, {'aluno_id': self.aluno.pk}).status_code, 200)
        self.assertEqual(Matricula.objects.count(), 1)

    def test_horarios_recusam_sobreposicao_e_aceitam_limite(self):
        self.autenticar()
        url = f'/api/ti/disciplinas/{self.disciplina.pk}/horarios/'
        self.assertEqual(self.enviar(url, {'dia': 0, 'inicio': '08:00', 'fim': '10:00'}).status_code, 201)
        self.assertEqual(self.enviar(url, {'dia': 0, 'inicio': '09:00', 'fim': '11:00'}).status_code, 400)
        self.assertEqual(self.enviar(url, {'dia': 0, 'inicio': '10:00', 'fim': '11:00'}).status_code, 201)
        self.assertEqual(Horario.objects.count(), 2)

    def test_modelo_horario_detecta_conflito_do_docente(self):
        Horario.objects.create(disciplina=self.disciplina, dia=0, inicio=time(8), fim=time(10))
        outra = Disciplina.objects.create(codigo='BD', nome='Banco de Dados', docente=self.docente)
        horario = Horario(disciplina=outra, dia=0, inicio=time(9), fim=time(11))
        with self.assertRaises(ValidationError):
            horario.full_clean()
        horario.inicio = time(10)
        horario.full_clean()

    def test_excluir_disciplina_remove_dependencias(self):
        self.registrar_aulas(1, 1)
        Horario.objects.create(disciplina=self.disciplina, dia=0, inicio=time(8), fim=time(10))
        self.autenticar()
        self.assertEqual(self.client.delete(f'/api/ti/disciplinas/{self.disciplina.pk}/').status_code, 200)
        for modelo in (Disciplina, Matricula, Aula, Presenca, Horario):
            with self.subTest(modelo=modelo.__name__):
                self.assertFalse(modelo.objects.exists())
        self.assertTrue(Aluno.objects.filter(pk=self.aluno.pk).exists())
        self.assertTrue(Docente.objects.filter(pk=self.docente.pk).exists())


if __name__ == '__main__':
    from django.test.runner import DiscoverRunner
    # Inclui também os testes de formulários administrativos já existentes.
    falhas = DiscoverRunner(verbosity=2).run_tests(['__main__', 'academico.tests'])
    sys.exit(bool(falhas))
