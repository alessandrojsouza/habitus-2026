from django.db import models
from django.contrib.auth.models import User
import secrets
from datetime import timedelta
from django.utils import timezone


class ConfirmacaoSenha(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='confirmacao_senha')
    token = models.CharField(max_length=100, unique=True, default=secrets.token_urlsafe)
    nova_senha = models.CharField(max_length=255)  # Armazena a senha criptografada temporariamente
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    confirmado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expira_em:
            # Token expira em 24 horas
            self.expira_em = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def expirado(self):
        return timezone.now() > self.expira_em

    def __str__(self):
        return f"Confirmação de senha - {self.user.username}"
