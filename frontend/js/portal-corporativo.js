/* =====================================================
   AcadSystem — Lógica do Portal Corporativo / TI
   Valida e cadastra alunos/docentes (espelha o app.py)
   ===================================================== */

let tipoCadastro = 'Aluno';

const REGRAS_ID = {
    Aluno:   { label: 'Matrícula',          exemplo: 'Ex: 202610293', perfil: 'Aluno',  pill: 'pill-blue' },
    Docente: { label: 'Número de registro', exemplo: 'Ex: 1234567',   perfil: 'Docente', pill: 'pill-green' }
};

const REGEX_EMAIL = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/;

document.addEventListener('DOMContentLoaded', () => {
    inicializarPortal('corporativo', 'Há 17 requerimentos aguardando análise.');

    configurarAtalhos();
    configurarTipoCadastro();
    configurarFormulario();
    configurarBuscaUsuarios();
    configurarReset();
});

/* Atalhos dos cards do painel (abrir cadastro / ir para gestão) */
function configurarAtalhos() {
    document.querySelectorAll('button[data-abrir]').forEach(btn => {
        btn.addEventListener('click', () => {
            definirTipo(btn.getAttribute('data-abrir'));
            const item = document.querySelector('.nav-item[data-target="cadastro"]');
            trocarSecao('cadastro', item);
        });
    });
    document.querySelectorAll('button[data-ir]').forEach(btn => {
        btn.addEventListener('click', () => {
            const alvo = btn.getAttribute('data-ir');
            const item = document.querySelector(`.nav-item[data-target="${alvo}"]`);
            trocarSecao(alvo, item);
        });
    });
}

/* Alterna entre Aluno e Docente no formulário */
function configurarTipoCadastro() {
    document.querySelectorAll('.tipo-btn').forEach(btn => {
        btn.addEventListener('click', () => definirTipo(btn.getAttribute('data-tipo')));
    });
}

function definirTipo(tipo) {
    tipoCadastro = tipo;
    const regra = REGRAS_ID[tipo];
    document.getElementById('tipo-cadastro').textContent = tipo;
    document.getElementById('label-id').textContent = regra.label;
    document.getElementById('c-id').placeholder = regra.exemplo;
    document.querySelectorAll('.tipo-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tipo') === tipo);
    });
}

/* Validação do cadastro — mesmas regras do app.py */
function configurarFormulario() {
    document.getElementById('form-cadastro').addEventListener('submit', e => {
        e.preventDefault();

        const nome = document.getElementById('c-nome').value.trim();
        const email = document.getElementById('c-email').value.trim();
        const id = document.getElementById('c-id').value.trim();
        const senha = document.getElementById('c-senha').value;
        const senha2 = document.getElementById('c-senha2').value;

        if (!nome || !email || !id || !senha || !senha2) {
            return mostrarToast('Preencha todos os campos!', 'erro');
        }
        if (!REGEX_EMAIL.test(email)) {
            return mostrarToast('Digite um e-mail válido. Ex: nome.sobrenome@uneb.br', 'erro');
        }
        if (senha !== senha2) {
            return mostrarToast('As senhas não conferem!', 'erro');
        }
        if (senha.length < 6) {
            return mostrarToast('A senha deve ter no mínimo 6 caracteres!', 'erro');
        }

        adicionarUsuario(nome, email, id, tipoCadastro);
        atualizarKpi(tipoCadastro);
        mostrarToast(`${tipoCadastro} ${nome} cadastrado(a) com sucesso!`, 'ok');
        e.target.reset();
    });
}

/* Insere a nova linha na tabela de usuários */
function adicionarUsuario(nome, email, id, tipo) {
    const tbody = document.querySelector('#tabela-usuarios tbody');
    const regra = REGRAS_ID[tipo];
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${nome}</td>
        <td>${email}</td>
        <td>${id}</td>
        <td><span class="pill ${regra.pill}">${tipo}</span></td>
        <td><button class="btn btn-light" data-reset>Redefinir senha</button></td>`;
    tbody.appendChild(tr);
    tr.querySelector('[data-reset]').addEventListener('click', () =>
        mostrarToast(`Senha de ${nome} redefinida. Uma senha temporária foi enviada por e-mail.`, 'ok'));
}

/* Atualiza o contador de alunos/docentes no painel */
function atualizarKpi(tipo) {
    const id = tipo === 'Aluno' ? 'kpi-alunos' : 'kpi-docentes';
    const el = document.getElementById(id);
    const atual = parseInt(el.textContent.replace(/\D/g, ''), 10) + 1;
    el.textContent = atual.toLocaleString('pt-BR');
}

/* Busca na tabela de usuários */
function configurarBuscaUsuarios() {
    const busca = document.getElementById('busca-usuarios');
    busca.addEventListener('input', () => {
        const termo = busca.value.toLowerCase();
        document.querySelectorAll('#tabela-usuarios tbody tr').forEach(tr => {
            tr.classList.toggle('hidden-row', !tr.textContent.toLowerCase().includes(termo));
        });
    });
}

/* Botões "Redefinir senha" já existentes na tabela */
function configurarReset() {
    document.querySelectorAll('#tabela-usuarios [data-reset]').forEach(btn => {
        btn.addEventListener('click', () => {
            const nome = btn.closest('tr').querySelector('td').textContent;
            mostrarToast(`Senha de ${nome} redefinida. Uma senha temporária foi enviada por e-mail.`, 'ok');
        });
    });
}
