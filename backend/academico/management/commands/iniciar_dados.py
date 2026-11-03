from datetime import time

from django.core.management.base import BaseCommand

from academico.models import (Aluno, Corporativo, Curso, Disciplina, Docente,
                              Horario, Matricula)

# Mesma conta de TI criada pelo login/app.py na primeira execução.
# TROQUE a senha após o primeiro acesso.
TI_INICIAL = {'nome': 'Administrador TI', 'usuario': 'admin',
              'email': 'ti@acadsystem.com', 'senha': 'admin123'}


class Command(BaseCommand):
    help = 'Cria a conta de TI inicial. Com --demo, cria também dados de exemplo.'

    def add_arguments(self, parser):
        parser.add_argument('--demo', action='store_true', help='Cria cursos, docente, alunos e disciplinas de exemplo')

    def handle(self, *args, **opts):
        if not Corporativo.objects.exists():
            ti = Corporativo(nome=TI_INICIAL['nome'], usuario=TI_INICIAL['usuario'], email=TI_INICIAL['email'])
            ti.definir_senha(TI_INICIAL['senha'])
            ti.save()
            self.stdout.write(self.style.SUCCESS(
                f"Conta de TI criada: usuário '{TI_INICIAL['usuario']}' / senha '{TI_INICIAL['senha']}'"))
        else:
            self.stdout.write('Conta de TI já existe.')

        if opts['demo']:
            self.criar_demo()

    def criar_demo(self):
        eng, _ = Curso.objects.get_or_create(nome='Engenharia de Computação')
        sis, _ = Curso.objects.get_or_create(nome='Sistemas de Informação')

        prof, criado = Docente.objects.get_or_create(
            registro='1234567',
            defaults={'nome': 'Ricardo Lima', 'email': 'ricardo.lima@uneb.br',
                      'departamento': 'Dpto. de Ciências Exatas'})
        if criado:
            prof.definir_senha('prof123')
            prof.save()

        alunos = []
        for nome, email, mat in [
            ('Maria Clara Souza', 'maria.souza@uneb.br', '202610293'),
            ('João Pedro Alves', 'joao.alves@uneb.br', '202610118'),
            ('Ana Beatriz Costa', 'ana.costa@uneb.br', '202610457'),
        ]:
            aluno, criado = Aluno.objects.get_or_create(
                matricula=mat, defaults={'nome': nome, 'email': email, 'curso': eng})
            if criado:
                aluno.definir_senha('aluno123')
                aluno.save()
            alunos.append(aluno)

        def disciplina(codigo, nome, curso, horarios):
            d, criada = Disciplina.objects.get_or_create(
                codigo=codigo, defaults={'nome': nome, 'curso': curso, 'docente': prof})
            if criada:
                for dia, ini, fim in horarios:
                    Horario.objects.create(disciplina=d, dia=dia, inicio=ini, fim=fim)
            return d

        calc = disciplina('MAT-A01', 'Cálculo Diferencial e Integral I', eng,
                          [(0, time(8), time(10)), (2, time(8), time(10))])
        alg = disciplina('DEX-011', 'Algoritmos e Estrutura de Dados I', sis,
                         [(1, time(10), time(12)), (3, time(10), time(12))])
        for aluno in alunos:
            Matricula.objects.get_or_create(aluno=aluno, disciplina=calc)
            Matricula.objects.get_or_create(aluno=aluno, disciplina=alg)

        self.stdout.write(self.style.SUCCESS(
            'Dados de exemplo criados. Docente: 1234567 / prof123. '
            'Alunos: e-mail (ex.: maria.souza@uneb.br) / aluno123.'))
