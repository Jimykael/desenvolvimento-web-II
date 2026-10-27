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

function salvarSessao(perfil, nome) {
    localStorage.setItem('acad_perfil', perfil);
    localStorage.setItem('acad_nome', nome || '');
}

function obterSessao() {
    return {
        perfil: localStorage.getItem('acad_perfil'),
        nome: localStorage.getItem('acad_nome')
    };
}

function encerrarSessao() {
    localStorage.removeItem('acad_perfil');
    localStorage.removeItem('acad_nome');
}

/* Protege um portal: se não houver sessão do perfil certo, volta ao login.
   (Protótipo — em produção a validação seria no servidor.) */
function protegerPortal(perfilEsperado) {
    const { perfil } = obterSessao();
    if (!perfil) {
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
    const { nome } = obterSessao();
    if (!nome) return;
    const elNome = document.querySelector('.topbar-user .u-name');
    if (elNome) elNome.textContent = nome;
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
