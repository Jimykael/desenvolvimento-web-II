/* =====================================================
   AcadSystem — Lógica da tela de login (index.html)
   ===================================================== */

// Rótulos de cada perfil (espelham as regras do app.py)
const ROTULOS = {
    aluno:       { label: 'E-mail institucional',                   exemplo: 'Ex: nome.sobrenome@uneb.br' },
    docente:     { label: 'E-mail institucional ou nº de registro', exemplo: 'Ex: 1234567 ou nome.sobrenome@uneb.br' },
    corporativo: { label: 'Usuário ou e-mail corporativo',          exemplo: 'Ex: admin ou ti@acadsystem.com' }
};

// Nome de exibição padrão por perfil (protótipo, sem backend)
const NOMES_DEMO = {
    aluno: 'Maria Clara Souza',
    docente: 'Prof. Dr. Ricardo Lima',
    corporativo: 'Administrador TI'
};

let perfilAtual = 'aluno';

document.addEventListener('DOMContentLoaded', () => {
    // Restaura "lembrar usuário", se existir
    const lembrado = localStorage.getItem('acad_lembrado');
    if (lembrado) {
        const dados = JSON.parse(lembrado);
        const botao = document.querySelector(`.tab[data-perfil="${dados.perfil}"]`);
        if (botao) selecionarPerfil(dados.perfil, botao);
        document.getElementById('usuario').value = dados.usuario || '';
        document.getElementById('lembrar').checked = true;
    }

    // Abas de perfil
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => selecionarPerfil(tab.getAttribute('data-perfil'), tab));
    });

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

    // Envio do formulário
    document.getElementById('form-login').addEventListener('submit', entrar);
});

function selecionarPerfil(perfil, botao) {
    perfilAtual = perfil;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    botao.classList.add('active');
    document.getElementById('labelUsuario').textContent = ROTULOS[perfil].label;
    document.getElementById('usuario').placeholder = ROTULOS[perfil].exemplo;
}

function entrar(e) {
    e.preventDefault();

    const usuario = document.getElementById('usuario').value.trim();
    const senha = document.getElementById('senha').value;

    // Validações equivalentes às do app.py
    if (!usuario || !senha) {
        mostrarToast('Por favor, preencha todos os campos.', 'erro');
        return;
    }
    if (perfilAtual === 'aluno' && !usuario.includes('@')) {
        mostrarToast('O acesso do aluno é feito pelo e-mail institucional.', 'erro');
        return;
    }
    if (senha.length < 4) {
        mostrarToast('Senha inválida. Verifique suas credenciais.', 'erro');
        return;
    }

    // "Lembrar meu usuário" (a senha nunca é salva — como no app.py)
    if (document.getElementById('lembrar').checked) {
        localStorage.setItem('acad_lembrado', JSON.stringify({ perfil: perfilAtual, usuario }));
    } else {
        localStorage.removeItem('acad_lembrado');
    }

    // Grava a sessão e redireciona para o portal do perfil
    const nome = NOMES_DEMO[perfilAtual];
    salvarSessao(perfilAtual, nome);

    mostrarToast('Login realizado! Redirecionando...', 'ok');
    setTimeout(() => {
        window.location.href = PERFIS_INFO[perfilAtual].pagina;
    }, 700);
}
