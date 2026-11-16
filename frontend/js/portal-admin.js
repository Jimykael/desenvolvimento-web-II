/* =====================================================
   AcadSystem — Portal de Administração
   Usa a API /api/ti/... (somente perfil "corporativo")
   ===================================================== */
let cursos = [];
let docentes = [];
let disciplinas = [];
let editandoCurso = null;       // id do curso em edição (null = novo)
let editandoDisciplina = null;  // id da disciplina em edição (null = nova)
let disciplinaAtual = null;     // disciplina aberta nos modais de horário/matrícula
let usuarioSenha = null;        // {tipo, id} do usuário que terá a senha redefinida

const $ = id => document.getElementById(id);

document.addEventListener('DOMContentLoaded', () => {
    inicializarPortal('corporativo');
    configurarModais();

    $('novo-usuario').addEventListener('click', abrirNovoUsuario);
    $('u-tipo').addEventListener('change', ajustarCamposUsuario);
    $('salvar-usuario').addEventListener('click', salvarUsuario);
    $('salvar-senha').addEventListener('click', salvarSenha);

    $('novo-curso').addEventListener('click', () => abrirCurso(null));
    $('salvar-curso').addEventListener('click', salvarCurso);

    $('nova-disciplina').addEventListener('click', () => abrirDisciplina(null));
    $('salvar-disciplina').addEventListener('click', salvarDisciplina);
    $('add-horario').addEventListener('click', adicionarHorario);
    $('add-matricula').addEventListener('click', adicionarMatricula);

    // Um clique na lista (delegação) evita registrar um listener por botão
    document.body.addEventListener('click', tratarAcao);

    carregarTudo();
});

async function carregarTudo() {
    try {
        const painel = await api('/ti/painel/');
        $('st-alunos').textContent = painel.alunos;
        $('st-docentes').textContent = painel.docentes;
        $('st-disciplinas').textContent = painel.disciplinas;
        await Promise.all([carregarUsuarios(), carregarCursos(), carregarDisciplinas()]);
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

/* ---------- Modais ---------- */
function abrir(id) { $(id).classList.add('show'); }
function fechar(id) { $(id).classList.remove('show'); }

function configurarModais() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('[data-close]').forEach(el =>
            el.addEventListener('click', () => modal.classList.remove('show')));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('show'); });
    });
}

function opcoes(lista, vazio, rotulo = x => x.nome) {
    return `<option value="">${esc(vazio)}</option>` +
        lista.map(x => `<option value="${x.id}">${esc(rotulo(x))}</option>`).join('');
}

/* Ações dos botões gerados dinamicamente: data-acao="nome" data-id="..." */
function tratarAcao(e) {
    const el = e.target.closest('[data-acao]');
    if (!el) return;
    const id = Number(el.dataset.id);
    const acoes = {
        'senha': () => abrirSenha(el.dataset.tipo, id, el.dataset.nome),
        'editar-curso': () => abrirCurso(id),
        'excluir-curso': () => excluirCurso(id),
        'editar-disc': () => abrirDisciplina(id),
        'excluir-disc': () => excluirDisciplina(id),
        'horarios': () => abrirHorarios(id),
        'rem-horario': () => removerHorario(id),
        'alunos': () => abrirMatriculas(id),
        'rem-matricula': () => removerMatricula(id),
    };
    if (acoes[el.dataset.acao]) acoes[el.dataset.acao]();
}

/* ====================== USUÁRIOS ====================== */
async function carregarUsuarios() {
    const dados = await api('/ti/usuarios/');
    $('tb-usuarios').innerHTML = dados.usuarios.map(u => `
        <tr>
            <td><span class="pill ${u.tipo === 'Aluno' ? 'pill-blue' : 'pill-green'}">${esc(u.tipo)}</span></td>
            <td>${esc(u.nome)}</td>
            <td>${esc(u.email)}</td>
            <td>${esc(u.identificador)}</td>
            <td><button class="btn btn-light" data-acao="senha" data-tipo="${esc(u.tipo)}" data-id="${u.id}" data-nome="${esc(u.nome)}">Redefinir senha</button></td>
        </tr>`).join('') || '<tr><td colspan="5">Nenhum usuário cadastrado.</td></tr>';
}

function ajustarCamposUsuario() {
    const aluno = $('u-tipo').value === 'Aluno';
    $('u-label-id').textContent = aluno ? 'Matrícula' : 'Registro';
    $('g-curso').style.display = aluno ? '' : 'none';
    $('g-depto').style.display = aluno ? 'none' : '';
}

function abrirNovoUsuario() {
    ['u-nome', 'u-email', 'u-identificador', 'u-depto', 'u-senha'].forEach(i => { $(i).value = ''; });
    $('u-tipo').value = 'Aluno';
    $('u-curso').innerHTML = opcoes(cursos, 'Sem curso');
    ajustarCamposUsuario();
    abrir('modal-usuario');
}

async function salvarUsuario() {
    const aluno = $('u-tipo').value === 'Aluno';
    const corpo = {
        tipo: $('u-tipo').value,
        nome: $('u-nome').value,
        email: $('u-email').value,
        identificador: $('u-identificador').value,
        senha: $('u-senha').value,
    };
    if (aluno) corpo.curso_id = $('u-curso').value || null;
    else corpo.departamento = $('u-depto').value;
    try {
        await api('/ti/cadastrar/', { method: 'POST', corpo });
        fechar('modal-usuario');
        mostrarToast('Usuário cadastrado.', 'ok');
        carregarTudo();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

function abrirSenha(tipo, id, nome) {
    usuarioSenha = { tipo, id };
    $('senha-quem').textContent = nome;
    $('nova-senha').value = '';
    abrir('modal-senha');
}

async function salvarSenha() {
    try {
        await api(`/ti/usuarios/${encodeURIComponent(usuarioSenha.tipo)}/${usuarioSenha.id}/senha/`,
            { method: 'POST', corpo: { senha: $('nova-senha').value } });
        fechar('modal-senha');
        mostrarToast('Senha redefinida.', 'ok');
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

/* ====================== CURSOS ====================== */
async function carregarCursos() {
    const dados = await api('/ti/cursos/');
    cursos = dados.cursos;
    $('tb-cursos').innerHTML = cursos.map(c => `
        <tr>
            <td>${esc(c.nome)}</td><td>${c.alunos}</td><td>${c.disciplinas}</td>
            <td>
                <button class="btn btn-light" data-acao="editar-curso" data-id="${c.id}">Editar</button>
                <button class="btn btn-light" data-acao="excluir-curso" data-id="${c.id}">Excluir</button>
            </td>
        </tr>`).join('') || '<tr><td colspan="4">Nenhum curso cadastrado.</td></tr>';
}

function abrirCurso(id) {
    editandoCurso = id;
    const c = cursos.find(x => x.id === id);
    $('curso-titulo').textContent = c ? 'Editar curso' : 'Novo curso';
    $('c-nome').value = c ? c.nome : '';
    abrir('modal-curso');
}

async function salvarCurso() {
    try {
        if (editandoCurso) {
            await api(`/ti/cursos/${editandoCurso}/`, { method: 'PUT', corpo: { nome: $('c-nome').value } });
        } else {
            await api('/ti/cursos/', { method: 'POST', corpo: { nome: $('c-nome').value } });
        }
        fechar('modal-curso');
        mostrarToast('Curso salvo.', 'ok');
        carregarTudo();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

async function excluirCurso(id) {
    if (!confirm('Excluir o curso? Alunos e disciplinas ficarão sem curso.')) return;
    try {
        await api(`/ti/cursos/${id}/`, { method: 'DELETE' });
        mostrarToast('Curso excluído.', 'ok');
        carregarTudo();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

/* ====================== DISCIPLINAS ====================== */
async function carregarDisciplinas() {
    const dados = await api('/ti/disciplinas/');
    aplicarDisciplinas(dados);
}

function aplicarDisciplinas(dados) {
    disciplinas = dados.disciplinas;
    docentes = dados.docentes;
    $('tb-disciplinas').innerHTML = disciplinas.map(d => `
        <tr>
            <td>${esc(d.codigo)}</td>
            <td>${esc(d.nome)}</td>
            <td>${esc(d.docente) || '—'}</td>
            <td>${esc(d.curso) || '—'}</td>
            <td>${d.horarios.map(h => esc(`${h.dia_nome.slice(0, 3)} ${h.inicio}-${h.fim}`)).join('<br>') || '—'}</td>
            <td>${d.alunos}</td>
            <td style="white-space:nowrap;">
                <button class="btn btn-light" data-acao="horarios" data-id="${d.id}">Horários</button>
                <button class="btn btn-light" data-acao="alunos" data-id="${d.id}">Alunos</button>
                <button class="btn btn-light" data-acao="editar-disc" data-id="${d.id}">Editar</button>
                <button class="btn btn-light" data-acao="excluir-disc" data-id="${d.id}">Excluir</button>
            </td>
        </tr>`).join('') || '<tr><td colspan="7">Nenhuma disciplina cadastrada.</td></tr>';
}

function abrirDisciplina(id) {
    editandoDisciplina = id;
    const d = disciplinas.find(x => x.id === id);
    $('disc-titulo').textContent = d ? 'Editar disciplina' : 'Nova disciplina';
    $('d-codigo').value = d ? d.codigo : '';
    $('d-nome').value = d ? d.nome : '';
    $('d-periodo').value = d ? d.periodo : '2026.1';
    $('d-carga').value = d ? d.carga_horaria : 68;
    $('d-curso').innerHTML = opcoes(cursos, 'Sem curso');
    $('d-docente').innerHTML = opcoes(docentes, 'Sem professor');
    $('d-curso').value = d && d.curso_id ? d.curso_id : '';
    $('d-docente').value = d && d.docente_id ? d.docente_id : '';
    abrir('modal-disciplina');
}

async function salvarDisciplina() {
    const corpo = {
        codigo: $('d-codigo').value,
        nome: $('d-nome').value,
        periodo: $('d-periodo').value,
        carga_horaria: $('d-carga').value,
        curso_id: $('d-curso').value || null,
        docente_id: $('d-docente').value || null,
    };
    try {
        if (editandoDisciplina) {
            await api(`/ti/disciplinas/${editandoDisciplina}/`, { method: 'PUT', corpo });
        } else {
            await api('/ti/disciplinas/', { method: 'POST', corpo });
        }
        fechar('modal-disciplina');
        mostrarToast('Disciplina salva.', 'ok');
        carregarTudo();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

async function excluirDisciplina(id) {
    if (!confirm('Excluir a disciplina? Horários, matrículas, aulas e presenças também serão removidos.')) return;
    try {
        await api(`/ti/disciplinas/${id}/`, { method: 'DELETE' });
        mostrarToast('Disciplina excluída.', 'ok');
        carregarTudo();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

/* ---------- Horários ---------- */
function abrirHorarios(id) {
    disciplinaAtual = id;
    renderizarHorarios();
    abrir('modal-horarios');
}

function renderizarHorarios() {
    const d = disciplinas.find(x => x.id === disciplinaAtual);
    $('hor-disciplina').textContent = `${d.nome} (${d.codigo}) · ${d.docente || 'sem professor'}`;
    $('hor-lista').innerHTML = d.horarios.map(h => `
        <div class="list-row">
            <span>${esc(h.dia_nome)} ${esc(h.inicio)} – ${esc(h.fim)}</span>
            <button class="btn btn-light" data-acao="rem-horario" data-id="${h.id}">Remover</button>
        </div>`).join('') || '<p class="page-sub">Sem horários cadastrados.</p>';
}

async function adicionarHorario() {
    try {
        await api(`/ti/disciplinas/${disciplinaAtual}/horarios/`, {
            method: 'POST',
            corpo: { dia: $('h-dia').value, inicio: $('h-inicio').value, fim: $('h-fim').value },
        });
        await carregarDisciplinas();
        renderizarHorarios();
        mostrarToast('Horário adicionado.', 'ok');
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

async function removerHorario(id) {
    try {
        await api(`/ti/horarios/${id}/`, { method: 'DELETE' });
        await carregarDisciplinas();
        renderizarHorarios();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

/* ---------- Matrículas ---------- */
async function abrirMatriculas(id) {
    disciplinaAtual = id;
    const d = disciplinas.find(x => x.id === id);
    $('mat-disciplina').textContent = `${d.nome} (${d.codigo})`;
    abrir('modal-matriculas');
    await carregarMatriculas();
}

async function carregarMatriculas(dados) {
    try {
        dados = dados || await api(`/ti/disciplinas/${disciplinaAtual}/matriculas/`);
    } catch (e) { mostrarToast(e.message, 'erro'); return; }
    $('mat-lista').innerHTML = dados.matriculas.map(m => `
        <div class="list-row">
            <span>${esc(m.aluno)} · ${esc(m.matricula)}</span>
            <button class="btn btn-light" data-acao="rem-matricula" data-id="${m.id}">Remover</button>
        </div>`).join('') || '<p class="page-sub">Nenhum aluno matriculado.</p>';
    $('m-aluno').innerHTML = opcoes(dados.disponiveis, 'Selecione um aluno', a => `${a.nome} (${a.matricula})`);
}

async function adicionarMatricula() {
    const alunoId = $('m-aluno').value;
    if (!alunoId) { mostrarToast('Selecione um aluno.', 'erro'); return; }
    try {
        const dados = await api(`/ti/disciplinas/${disciplinaAtual}/matriculas/`,
            { method: 'POST', corpo: { aluno_id: Number(alunoId) } });
        await carregarMatriculas(dados);
        carregarDisciplinas();
        mostrarToast('Aluno matriculado.', 'ok');
    } catch (e) { mostrarToast(e.message, 'erro'); }
}

async function removerMatricula(id) {
    if (!confirm('Remover a matrícula? As notas do aluno nesta disciplina serão perdidas.')) return;
    try {
        await api(`/ti/matriculas/${id}/`, { method: 'DELETE' });
        await carregarMatriculas();
        carregarDisciplinas();
    } catch (e) { mostrarToast(e.message, 'erro'); }
}
