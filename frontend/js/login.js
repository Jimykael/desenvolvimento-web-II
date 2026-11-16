/* =====================================================
   AcadSystem — Lógica da tela de login (index.html)
   Login único: o servidor identifica o perfil pelo e-mail e senha.
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Restaura "lembrar usuário", se existir
    try {
        const lembrado = JSON.parse(localStorage.getItem('acad_lembrado') || 'null');
        if (lembrado && lembrado.usuario) {
            document.getElementById('usuario').value = lembrado.usuario;
            document.getElementById('lembrar').checked = true;
        }
    } catch (e) {
        localStorage.removeItem('acad_lembrado');
    }

    // Mostrar/ocultar senha
    const toggle = document.getElementById('toggle-senha');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const campo = document.getElementById('senha');
            const mostrar = campo.type === 'password';
            campo.type = mostrar ? 'text' : 'password';
            toggle.textContent = mostrar ? '🙈' : '👁️';
        });
    }

    document.getElementById('form-login').addEventListener('submit', entrar);
});

function entrar(e) {
    e.preventDefault();

    const email = document.getElementById('usuario').value.trim();
    const senha = document.getElementById('senha').value;

    if (!email || !senha) {
        mostrarToast('Por favor, preencha todos os campos.', 'erro');
        return;
    }
    if (!email.includes('@')) {
        mostrarToast('Informe o e-mail cadastrado.', 'erro');
        return;
    }

    encerrarSessao(); // descarta token antigo antes de tentar de novo
    const botao = document.querySelector('.btn-entrar');
    botao.disabled = true;

    api('/login/', {
        method: 'POST',
        corpo: { email, senha }
    }).then(dados => {
        // "Lembrar meu usuário" (a senha nunca é salva)
        if (document.getElementById('lembrar').checked) {
            localStorage.setItem('acad_lembrado', JSON.stringify({ usuario: email }));
        } else {
            localStorage.removeItem('acad_lembrado');
        }

        salvarSessao(dados.perfil, dados.nome, dados.token, dados.detalhe);
        mostrarToast('Login realizado! Redirecionando...', 'ok');
        setTimeout(() => {
            window.location.href = PERFIS_INFO[dados.perfil].pagina;
        }, 500);
    }).catch(err => {
        mostrarToast(err.message, 'erro');
        botao.disabled = false;
    });
}
