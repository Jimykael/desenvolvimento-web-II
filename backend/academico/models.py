from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class ContaMixin(models.Model):
    """Comportamento comum às contas de acesso (senha sempre criptografada)."""

    senha = models.CharField(max_length=256)

    class Meta:
        abstract = True

    def definir_senha(self, senha_pura):
        self.senha = make_password(senha_pura)

    def conferir_senha(self, senha_pura):
        return check_password(senha_pura, self.senha)


class Curso(models.Model):
    nome = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Aluno(ContaMixin):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    matricula = models.CharField(max_length=30, unique=True)
    curso = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL, related_name='alunos')

    class Meta:
        ordering = ['nome']

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.matricula})'


class Docente(ContaMixin):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    registro = models.CharField(max_length=30, unique=True)
    departamento = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['nome']

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.registro})'


class Corporativo(ContaMixin):
    nome = models.CharField(max_length=150)
    usuario = models.CharField(max_length=60, unique=True)
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = 'Usuário corporativo (TI)'
        verbose_name_plural = 'Usuários corporativos (TI)'

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        self.usuario = self.usuario.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Disciplina(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=150)
    carga_horaria = models.PositiveIntegerField(default=68)
    periodo = models.CharField(max_length=10, default='2026.1')
    curso = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL, related_name='disciplinas')
    docente = models.ForeignKey(Docente, null=True, blank=True, on_delete=models.SET_NULL, related_name='disciplinas')
    ementa = models.TextField(blank=True)
    bibliografia = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.codigo})'


class Horario(models.Model):
    DIAS = [(0, 'Segunda'), (1, 'Terça'), (2, 'Quarta'), (3, 'Quinta'), (4, 'Sexta'), (5, 'Sábado')]

    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='horarios')
    dia = models.PositiveSmallIntegerField(choices=DIAS)
    inicio = models.TimeField()
    fim = models.TimeField()

    class Meta:
        ordering = ['dia', 'inicio']

    def __str__(self):
        return f'{self.disciplina.codigo} - {self.get_dia_display()} {self.inicio:%H:%M}'


class Matricula(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='matriculas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='matriculas')
    n1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    n2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [('aluno', 'disciplina')]

    def __str__(self):
        return f'{self.aluno.nome} em {self.disciplina.codigo}'


class Aula(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='aulas')
    data = models.DateField()

    class Meta:
        unique_together = [('disciplina', 'data')]
        ordering = ['-data']

    def __str__(self):
        return f'{self.disciplina.codigo} - {self.data:%d/%m/%Y}'


class Presenca(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='presencas')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='presencas')
    presente = models.BooleanField(default=True)

    class Meta:
        unique_together = [('aula', 'aluno')]
