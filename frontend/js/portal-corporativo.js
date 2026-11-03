/* =====================================================
   AcadSystem — Lógica do Portal Corporativo / TI
   Cadastra e gerencia alunos/docentes via API (/api/ti/...)
   ===================================================== */

let tipoCadastro = 'Aluno';

const REGRAS_ID = {
    Aluno:   { label: 'Matrícula',          exemplo: 'Ex: 202610293', pill: 'pill-blue' },
    Docente: { label: 'Número de registro', exemplo: 'Ex: 1234567',   pill: 'pill-green' }
};

const REGEX_EMAIL = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/;

document.addEventListener('DOMContentLoaded', () => {
    inicializarPortal('corporativo', 'Você não possui novos avisos.');

    configurarAtalhos();
    configurarTipoCadastro();
    configurarFormulario();
    configurarBuscaUsuarios();
    carregarPainel();
    carregarUsuarios();
});

/* KPIs e lista de cursos */
async function carregarPainel() {
    try {
        const d = await api('/ti/painel/');
        document.getElementById('kpi-alunos').textContent = d.alunos.toLocaleString('pt-BR');
        document.getElementById('kpi-docentes').textContent = d.docentes.toLocaleString('pt-BR');
        document.getElementById('kpi-disciplinas').textContent = d.disciplinas.toLocaleString('pt-BR');
        document.getElementById('c-curso').innerHTML = '<option value="">Sem curso</option>' +
            d.cursos.map(c => `<option value="${c.id}">${esc(c.nome)}</option>`).join('');
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

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
    document.getElementById('grupo-curso').style.display = tipo === 'Aluno' ? '' : 'none';
    document.getElementById('grupo-depto').style.display = tipo === 'Docente' ? '' : 'none';
    document.querySelectorAll('.tipo-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tipo') === tipo);
    });
}

/* Cadastro: valida no navegador e o servidor valida novamente */
function configurarFormulario() {
    document.getElementById('form-cadastro').addEventListener('submit', async e => {
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

        const corpo = { tipo: tipoCadastro, nome, email, identificador: id, senha };
        if (tipoCadastro === 'Aluno') corpo.curso_id = document.getElementById('c-curso').value || null;
        else corpo.departamento = document.getElementById('c-depto').value.trim();

        try {
            await api('/ti/cadastrar/', { method: 'POST', corpo });
            mostrarToast(`${tipoCadastro} ${nome} cadastrado(a) com sucesso!`, 'ok');
            e.target.reset();
            carregarPainel();
            carregarUsuarios();
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    });
}

/* Tabela de usuários */
async function carregarUsuarios() {
    const tbody = document.querySelector('#tabela-usuarios tbody');
    try {
        const { usuarios } = await api('/ti/usuarios/');
        tbody.innerHTML = usuarios.length ? usuarios.map(u => `
            <tr>
                <td>${esc(u.nome)}</td>
                <td>${esc(u.email)}</td>
                <td>${esc(u.identificador)}</td>
                <td><span class="pill ${REGRAS_ID[u.tipo].pill}">${esc(u.tipo)}</span></td>
                <td><button class="btn btn-light" data-reset data-tipo="${esc(u.tipo)}" data-id="${u.id}" data-nome="${esc(u.nome)}">Redefinir senha</button></td>
            </tr>`).join('')
            : '<tr><td colspan="5">Nenhum usuário cadastrado.</td></tr>';
        tbody.querySelectorAll('[data-reset]').forEach(btn => btn.addEventListener('click', () => redefinirSenha(btn)));
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

async function redefinirSenha(btn) {
    const nome = btn.getAttribute('data-nome');
    const nova = window.prompt(`Nova senha para ${nome} (mínimo 6 caracteres):`);
    if (nova === null) return; // cancelou
    try {
        await api(`/ti/usuarios/${btn.getAttribute('data-tipo')}/${btn.getAttribute('data-id')}/senha/`, {
            method: 'POST',
            corpo: { senha: nova }
        });
        mostrarToast(`Senha de ${nome} redefinida com sucesso.`, 'ok');
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
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
