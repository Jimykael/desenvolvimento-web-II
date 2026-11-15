from django.contrib.auth.hashers import check_password
from django.test import TestCase

from .admin import AlunoAdminForm, DocenteAdminForm
from .models import Aluno


class ContaAdminFormTests(TestCase):
    def test_aluno_cadastrado_pelo_admin_recebe_senha_com_hash(self):
        form = AlunoAdminForm(data={
            'nome': 'Ana Souza',
            'email': 'ANA@EXEMPLO.COM',
            'senha': 'senha-segura',
            'matricula': '2026001',
            'curso': '',
        })

        self.assertTrue(form.is_valid(), form.errors)
        aluno = form.save()

        self.assertEqual(aluno.email, 'ana@exemplo.com')
        self.assertTrue(check_password('senha-segura', aluno.senha))
        self.assertNotEqual(aluno.senha, 'senha-segura')

    def test_docente_cadastrado_pelo_admin_recebe_senha_com_hash(self):
        form = DocenteAdminForm(data={
            'nome': 'Carlos Lima',
            'email': 'carlos@exemplo.com',
            'senha': 'senha-segura',
            'registro': 'D123',
            'departamento': 'Exatas',
        })

        self.assertTrue(form.is_valid(), form.errors)
        docente = form.save()

        self.assertTrue(check_password('senha-segura', docente.senha))

    def test_edicao_sem_senha_preserva_a_senha_atual(self):
        aluno = Aluno(
            nome='Ana Souza',
            email='ana@exemplo.com',
            matricula='2026001',
        )
        aluno.definir_senha('senha-anterior')
        aluno.save()

        form = AlunoAdminForm(data={
            'nome': 'Ana Souza Atualizada',
            'email': 'ana@exemplo.com',
            'senha': '',
            'matricula': '2026001',
            'curso': '',
        }, instance=aluno)

        self.assertTrue(form.is_valid(), form.errors)
        aluno = form.save()

        self.assertTrue(check_password('senha-anterior', aluno.senha))

    def test_senha_curta_nao_e_aceita(self):
        form = DocenteAdminForm(data={
            'nome': 'Carlos Lima',
            'email': 'carlos@exemplo.com',
            'senha': '12345',
            'registro': 'D123',
            'departamento': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('senha', form.errors)

    def test_senha_e_obrigatoria_no_cadastro(self):
        form = AlunoAdminForm(data={
            'nome': 'Ana Souza',
            'email': 'ana@exemplo.com',
            'senha': '',
            'matricula': '2026001',
            'curso': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('senha', form.errors)
