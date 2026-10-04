"""
Testes de autenticação híbrida: username OU email OU RM.
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestLoginHibrido:

    def test_login_com_username(self, client, usuario_coordenador):
        """Login com username funciona."""
        resp = client.post(reverse('login'), {
            'username': 'coord1',
            'password': 'senha123',
        })
        # 302 = redirect após login bem-sucedido
        assert resp.status_code == 302
        assert '_auth_user_id' in client.session

    def test_login_com_email(self, client, usuario_coordenador):
        """Login com email funciona (login híbrido)."""
        resp = client.post(reverse('login'), {
            'username': 'coord1@reabitech.test',
            'password': 'senha123',
        })
        assert resp.status_code == 302
        assert '_auth_user_id' in client.session

    def test_login_invalido_nao_autentica(self, client, usuario_coordenador):
        """Senha errada não autentica."""
        resp = client.post(reverse('login'), {
            'username': 'coord1',
            'password': 'senhaerrada',
        })
        assert '_auth_user_id' not in client.session

    def test_usuario_anonimo_e_redirecionado(self, client):
        """Acessar dashboard sem login redireciona."""
        resp = client.get(reverse('dashboard:dashboard'))
        assert resp.status_code == 302
        assert 'login' in resp.url.lower() or resp.url.startswith('/login')


@pytest.mark.django_db
class TestPerfis:

    def test_todos_perfis_criados(self, usuario_coordenador, usuario_fisio,
                                   usuario_tecnico, usuario_psicologo,
                                   usuario_atleta):
        """Cada usuário tem exatamente 1 Perfil com tipo correto."""
        assert usuario_coordenador.perfil.tipo == 'coordenador'
        assert usuario_fisio.perfil.tipo == 'fisioterapeuta'
        assert usuario_tecnico.perfil.tipo == 'tecnico'
        assert usuario_psicologo.perfil.tipo == 'psicologo'
        assert usuario_atleta.perfil.tipo == 'atleta'

    def test_atleta_tem_rm(self, atleta):
        """Atleta oficial tem RM."""
        assert atleta.rm == '12345'
        assert atleta.usuario.username == 'atleta1'
