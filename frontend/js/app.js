/* =====================================================
   AcadSystem — JavaScript compartilhado dos portais
   Funções reutilizadas em todas as páginas internas
   ===================================================== */

/* ---------------- SESSÃO (localStorage) ----------------
   O login (index.html) grava o perfil e o nome do usuário.
   Cada portal valida se o perfil corresponde à página. */

const PERFIS_INFO = {
    aluno:       { pagina: 'portal-aluno.html',       rotulo: 'Discente' },
    docente:     { pagina: 'portal-professor.html',   rotulo: 'Docente' },
    corporativo: { pagina: 'portal-corporativo.html', rotulo: 'Corporativo / TI' }
};

/* ---------------- API ----------------
   Se a página foi aberta pelo Django (porta 8000), usa caminho relativo.
   Se foi aberta por outro servidor (ex.: Live Server), aponta para o Django. */
const API_BASE = window.location.port === '8000' ? '/api' : 'http://127.0.0.1:8000/api';

/* Chamada à API com token. Retorna o JSON ou lança Error(mensagem). */
async function api(caminho, opcoes = {}) {
    const { token } = obterSessao();
    const config = {
        method: opcoes.method || 'GET',
        headers: { 'Content-Type': 'application/json' }
    };
    if (token) config.headers['Authorization'] = 'Bearer ' + token;
    if (opcoes.corpo !== undefined) config.body = JSON.stringify(opcoes.corpo);

    let resposta;
    try {
        resposta = await fetch(API_BASE + caminho, config);
    } catch (e) {
        throw new Error('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
    }
    let dados = {};
    try { dados = await resposta.json(); } catch (e) { /* resposta sem corpo */ }

    // Token expirado/inválido fora da tela de login: volta ao login
    if (resposta.status === 401 && token) {
        encerrarSessao();
        window.location.href = 'index.html';
        throw new Error(dados.erro || 'Sessão expirada.');
    }
    if (!resposta.ok) throw new Error(dados.erro || 'Erro inesperado no servidor.');
    return dados;
}

/* Escapa texto antes de inserir em innerHTML (evita XSS com dados do banco) */
function esc(texto) {
    return String(texto ?? '').replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmtNum(valor, sufixo = '') {
    return valor === null || valor === undefined
        ? '—'
        : String(valor).replace('.', ',') + sufixo;
}

function salvarSessao(perfil, nome, token, detalhe) {
    localStorage.setItem('acad_perfil', perfil);
    localStorage.setItem('acad_nome', nome || '');
    localStorage.setItem('acad_token', token || '');
    localStorage.setItem('acad_detalhe', detalhe || '');
}

function obterSessao() {
    return {
        perfil: localStorage.getItem('acad_perfil'),
        nome: localStorage.getItem('acad_nome'),
        token: localStorage.getItem('acad_token'),
        detalhe: localStorage.getItem('acad_detalhe')
    };
}

function encerrarSessao() {
    ['acad_perfil', 'acad_nome', 'acad_token', 'acad_detalhe'].forEach(k => localStorage.removeItem(k));
}

/* Protege um portal: se não houver sessão do perfil certo, volta ao login.
   A validação real é feita pelo servidor a cada chamada da API. */
function protegerPortal(perfilEsperado) {
    const { perfil, token } = obterSessao();
    if (!perfil || !token) {
        window.location.href = 'index.html';
        return false;
    }
    if (perfil !== perfilEsperado) {
        // Perfil logado é outro: redireciona para o portal correto
        window.location.href = PERFIS_INFO[perfil].pagina;
        return false;
    }
    return true;
}

function logout() {
    encerrarSessao();
    window.location.href = 'index.html';
}

/* ---------------- TOAST ---------------- */
function mostrarToast(mensagem, tipo) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        toast.innerHTML = '<span class="t-ico">ℹ️</span><span class="t-msg"></span>';
        document.body.appendChild(toast);
    }
    toast.querySelector('.t-ico').textContent =
        tipo === 'erro' ? '⛔' : tipo === 'ok' ? '✅' : 'ℹ️';
    toast.querySelector('.t-msg').textContent = mensagem;

    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), 3500);
}

/* ---------------- NAVEGAÇÃO ENTRE SEÇÕES ----------------
   Cada portal tem <section data-view="..."> e itens de menu
   com data-target="...". Trocamos a seção sem recarregar. */
function inicializarNavegacao() {
    const itens = document.querySelectorAll('.nav-item[data-target]');
    itens.forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const alvo = item.getAttribute('data-target');
            trocarSecao(alvo, item);
        });
    });
}

function trocarSecao(alvo, itemAtivo) {
    document.querySelectorAll('[data-view]').forEach(sec => {
        sec.style.display = sec.getAttribute('data-view') === alvo ? '' : 'none';
    });
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    if (itemAtivo) itemAtivo.classList.add('active');

    // Atualiza o breadcrumb, se houver rótulo definido no item
    const crumb = document.querySelector('.breadcrumb .here');
    if (crumb && itemAtivo) {
        const texto = itemAtivo.querySelector('span:last-child');
        if (texto) crumb.textContent = texto.textContent;
    }

    // Rola o conteúdo de volta ao topo
    const content = document.querySelector('.content');
    if (content) content.scrollTop = 0;
}

/* ---------------- NOTIFICAÇÕES (sino) ---------------- */
function inicializarSino(mensagem) {
    const sino = document.querySelector('.bell');
    if (sino) {
        sino.addEventListener('click', () => {
            mostrarToast(mensagem || 'Você não tem novas notificações.');
            const dot = sino.querySelector('.dot');
            if (dot) dot.style.display = 'none';
        });
    }
}

/* ---------------- LOGOUT ---------------- */
function inicializarLogout() {
    document.querySelectorAll('[data-action="logout"]').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            logout();
        });
    });
}

/* ---------------- RELÓGIO NA TOPBAR ---------------- */
function inicializarRelogio() {
    const el = document.getElementById('relogio');
    if (!el) return;
    const atualizar = () => {
        const agora = new Date();
        const data = agora.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
        const hora = agora.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        el.textContent = `${data} · ${hora}`;
    };
    atualizar();
    setInterval(atualizar, 30000);
}

/* ---------------- PREENCHER DADOS DA SESSÃO ----------------
   Se o login gravou o nome do usuário, exibe-o na topbar. */
function preencherUsuario() {
    const { nome, detalhe } = obterSessao();
    if (!nome) return;
    const elNome = document.querySelector('.topbar-user .u-name');
    if (elNome) elNome.textContent = nome;
    const elRole = document.querySelector('.topbar-user .u-role');
    if (elRole && detalhe) elRole.textContent = detalhe;
    const avatar = document.querySelector('.topbar-user .avatar');
    if (avatar) {
        const iniciais = nome.trim().split(/\s+/).map(p => p[0]).slice(0, 2).join('').toUpperCase();
        if (iniciais) avatar.textContent = iniciais;
    }
    // Atualiza também a saudação do título, se existir
    const saudacao = document.querySelector('[data-saudacao]');
    if (saudacao) {
        const primeiro = nome.trim().split(/\s+/)[0];
        saudacao.textContent = saudacao.getAttribute('data-saudacao').replace('{nome}', primeiro);
    }
}

/* ---------------- INICIALIZAÇÃO COMUM DE PORTAL ---------------- */
function inicializarPortal(perfilEsperado, msgSino) {
    if (!protegerPortal(perfilEsperado)) return;
    preencherUsuario();
    inicializarNavegacao();
    inicializarSino(msgSino);
    inicializarLogout();
    inicializarRelogio();
}
