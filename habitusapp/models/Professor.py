from django.db import models
from datetime import date
from django.contrib.auth.models import User

class Professor(models.Model):
    class Tipo_Trabalho(models.TextChoices):
        PROFESSOR = 'Professor(a)', 'Professor(a)'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(null=True, blank=True, upload_to='foto-perfil-professor/')
    nome = models.CharField(max_length=100)
    data_nasc = models.DateField()
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    cpf = models.CharField(max_length=14, unique=True, editable=False)
    
    inst_formacao = models.CharField(max_length=100, blank=True, null=True)
    data_admissao = models.DateField()
    tipo_trabalho = models.CharField(
        max_length=20,
        choices=Tipo_Trabalho.choices,
        default=Tipo_Trabalho.PROFESSOR
    )

    @property
    def idade(self):
        today = date.today()
        idade = today.year - self.data_nasc.year - ((today.month, today.day) < (self.data_nasc.month, self.data_nasc.day))
        return idade

    def __str__(self):
        return f"{self.nome} ({self.matricula}) ({self.idade})"

    @property
    def pode_acessar(self):
        return self.ativo and self.user.is_active
