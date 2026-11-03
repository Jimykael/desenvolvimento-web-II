/* =====================================================
   AcadSystem — Portal TI: Cursos, Disciplinas, Horários e Matrículas
   Usa api(), esc() e mostrarToast() de app.js
   ===================================================== */

let cursoEditando = null;       // id do curso em edição
let disciplinaEditando = null;  // id da disciplina em edição
let disciplinas = [];           // cache da última listagem
let disciplinaModal = null;     // disciplina aberta nos modais

document.addEventListener('DOMContentLoaded', () => {
    configurarCursos();
    configurarDisciplinas();
    configurarModais();
    carregarCursos();
    carregarDisciplinas();
});

/* ======================= CURSOS ======================= */
function configurarCursos() {
    document.getElementById('form-curso').addEventListener('submit', async e => {
        e.preventDefault();
        const nome = document.getElementById('curso-nome').value.trim();
        if (!nome) return mostrarToast('Informe o nome do curso.', 'erro');
        try {
            if (cursoEditando) {
                await api(`/ti/cursos/${cursoEditando}/`, { method: 'PUT', corpo: { nome } });
                mostrarToast('Curso atualizado.', 'ok');
            } else {
                await api('/ti/cursos/', { method: 'POST', corpo: { nome } });
                mostrarToast('Curso cadastrado.', 'ok');
            }
            cancelarEdicaoCurso();
            await Promise.all([carregarCursos(), carregarDisciplinas()]);
            carregarPainel(); // atualiza o select de cursos do cadastro de alunos
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    });
    document.getElementById('curso-cancelar').addEventListener('click', cancelarEdicaoCurso);
}

function cancelarEdicaoCurso() {
    cursoEditando = null;
    document.getElementById('curso-nome').value = '';
    document.getElementById('label-curso').textContent = 'Novo curso';
    document.getElementById('curso-salvar').textContent = 'Adicionar Curso';
    document.getElementById('curso-cancelar').style.display = 'none';
}

async function carregarCursos() {
    const tbody = document.querySelector('#tabela-cursos tbody');
    try {
        const { cursos } = await api('/ti/cursos/');
        tbody.innerHTML = cursos.length ? cursos.map(c => `
            <tr>
                <td>${esc(c.nome)}</td><td>${c.alunos}</td><td>${c.disciplinas}</td>
                <td style="display:flex;gap:8px;">
                    <button class="btn btn-light" data-editar="${c.id}" data-nome="${esc(c.nome)}">Editar</button>
                    <button class="btn btn-light" data-excluir="${c.id}" data-nome="${esc(c.nome)}">Excluir</button>
                </td>
            </tr>`).join('')
            : '<tr><td colspan="4">Nenhum curso cadastrado.</td></tr>';

        tbody.querySelectorAll('[data-editar]').forEach(btn => btn.addEventListener('click', () => {
            cursoEditando = btn.getAttribute('data-editar');
            document.getElementById('curso-nome').value = btn.getAttribute('data-nome');
            document.getElementById('label-curso').textContent = 'Editando curso';
            document.getElementById('curso-salvar').textContent = 'Salvar Alterações';
            document.getElementById('curso-cancelar').style.display = '';
            document.getElementById('curso-nome').focus();
        }));
        tbody.querySelectorAll('[data-excluir]').forEach(btn => btn.addEventListener('click', async () => {
            const nome = btn.getAttribute('data-nome');
            if (!confirm(`Excluir o curso "${nome}"?\nAlunos e disciplinas vinculados ficarão sem curso.`)) return;
            try {
                await api(`/ti/cursos/${btn.getAttribute('data-excluir')}/`, { method: 'DELETE' });
                mostrarToast('Curso excluído.', 'ok');
                if (cursoEditando) cancelarEdicaoCurso();
                await Promise.all([carregarCursos(), carregarDisciplinas()]);
                carregarPainel();
            } catch (err) {
                mostrarToast(err.message, 'erro');
            }
        }));
    } catch (err) {
        mostrarToast(err.message, 'erro');
    }
}

/* ======================= DISCIPLINAS ======================= */
function configurarDisciplinas() {
    document.getElementById('form-disciplina').addEventListener('submit', async e => {
        e.preventDefault();
        const corpo = {
            codigo: document.getElementById('d-codigo').value.trim(),
            nome: document.getElementById('d-nome').value.trim(),
            carga_horaria: document.getElementById('d-carga').value,
            periodo: document.getElementById('d-periodo').value.trim(),
            curso_id: document.getElementById('d-curso').value || null,
            docente_id: document.getElementById('d-docente').value || null
        };
        if (!corpo.codigo || !corpo.nome) return mostrarToast('Informe o código e o nome da disciplina.', 'erro');
        try {
            if (disciplinaEditando) {
                await api(`/ti/disciplinas/${disciplinaEditando}/`, { method: 'PUT', corpo });
                mostrarToast('Disciplina atualizada.', 'ok');
            } else {
                await api('/ti/disciplinas/', { method: 'POST', corpo });
                mostrarToast('Disciplina cadastrada.', 'ok');
            }
            cancelarEdicaoDisciplina();
            await carregarDisciplinas();
            carregarPainel();
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    });
    document.getElementById('d-cancelar').addEventListener('click', cancelarEdicaoDisciplina);

    document.getElementById('busca-disciplinas').addEventListener('input', e => {
        const termo = e.target.value.toLowerCase();
        document.querySelectorAll('#tabela-disciplinas tbody tr').forEach(tr => {
            tr.classList.toggle('hidden-row', !tr.textContent.toLowerCase().includes(termo));
        });
    });
}

function cancelarEdicaoDisciplina() {
    disciplinaEditando = null;
    document.getElementById('form-disciplina').reset();
    document.getElementById('d-carga').value = 68;
    document.getElementById('d-periodo').value = '2026.1';
    document.getElementById('label-disciplina').textContent = 'Nova Disciplina';
    document.getElementById('d-salvar').textContent = 'Adicionar Disciplina';
    document.getElementById('d-cancelar').style.display = 'none';
}

function preencherSelect(id, itens, vazio, selecionado) {
    const sel = document.getElementById(id);
    const atual = selecionado !== undefined ? selecionado : sel.value;
    sel.innerHTML = `<option value="">${vazio}</option>` +
        itens.map(i => `<option value="${i.id}">${esc(i.nome)}</option>`).join('');
    sel.value = atual ? String(atual) : '';
}

async function carregarDisciplinas() {
    const tbody = document.querySelector('#tabela-disciplinas tbody');
    try {
        const dados = await api('/ti/disciplinas/');
        disciplinas = dados.disciplinas;
        preencherSelect('d-curso', dados.cursos, 'Sem curso');
        preencherSelect('d-docente', dados.docentes, 'Sem docente');

        tbody.innerHTML = disciplinas.length ? disciplinas.map(d => `
            <tr>
                <td>${esc(d.codigo)}</td>
                <td>${esc(d.nome)}<br><small style="color:var(--text-muted);">${esc(d.periodo)} · ${d.carga_horaria}h</small></td>
                <td>${esc(d.curso) || '—'}</td>
                <td>${esc(d.docente) || '—'}</td>
                <td>${d.horarios.length
                    ? d.horarios.map(h => `${esc(h.dia_nome.slice(0, 3))} ${h.inicio}–${h.fim}`).join('<br>')
                    : '—'}</td>
                <td>${d.alunos}</td>
                <td>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;">
                        <button class="btn btn-light" data-acao="editar" data-id="${d.id}">Editar</button>
                        <button class="btn btn-light" data-acao="horarios" data-id="${d.id}">Horários</button>
                        <button class="btn btn-light" data-acao="matriculas" data-id="${d.id}">Matrículas</button>
                        <button class="btn btn-light" data-acao="excluir" data-id="${d.id}">Excluir</button>
                    </div>
                </td>
            </tr>`).join('')
            : '<tr><td colspan="7">Nenhuma disciplina cadastrada.</td></tr>';

        tbody.querySelectorAll('[data-acao]').forEach(btn => btn.addEventListener('click', () => {
            const d = disciplinas.find(x => x.id === Number(btn.getAttribute('data-id')));
            const acao = btn.getAttribute('data-acao');
            if (acao === 'editar') editarDisciplina(d);
            else if (acao === 'horarios') abrirHorarios(d);
            else if (acao === 'matriculas') abrirMatriculas(d);
            else excluirDisciplina(d);
        }));

        // Se um modal está aberto, atualiza o título/lista com os dados novos
        if (disciplinaModal) {
            disciplinaModal = disciplinas.find(x => x.id === disciplinaModal.id) || null;
            if (document.getElementById('modal-horarios').classList.contains('show') && disciplinaModal) {
                renderizarHorarios();
            }
        }
    } catch (err) {
        mostrarToast(err.message, 'erro');
    }
}

function editarDisciplina(d) {
    disciplinaEditando = d.id;
    document.getElementById('d-codigo').value = d.codigo;
    document.getElementById('d-nome').value = d.nome;
    document.getElementById('d-carga').value = d.carga_horaria;
    document.getElementById('d-periodo').value = d.periodo;
    document.getElementById('d-curso').value = d.curso_id ? String(d.curso_id) : '';
    document.getElementById('d-docente').value = d.docente_id ? String(d.docente_id) : '';
    document.getElementById('label-disciplina').textContent = `Editando ${d.codigo}`;
    document.getElementById('d-salvar').textContent = 'Salvar Alterações';
    document.getElementById('d-cancelar').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.querySelector('.content').scrollTop = 0;
}

async function excluirDisciplina(d) {
    if (!confirm(`Excluir "${d.nome}" (${d.codigo})?\nIsso apaga também horários, matrículas, notas e frequências desta disciplina.`)) return;
    try {
        await api(`/ti/disciplinas/${d.id}/`, { method: 'DELETE' });
        mostrarToast('Disciplina excluída.', 'ok');
        if (disciplinaEditando === d.id) cancelarEdicaoDisciplina();
        await carregarDisciplinas();
        carregarPainel();
    } catch (err) {
        mostrarToast(err.message, 'erro');
    }
}

/* ======================= MODAIS ======================= */
function configurarModais() {
    ['modal-horarios', 'modal-matriculas'].forEach(id => {
        const modal = document.getElementById(id);
        modal.querySelectorAll('[data-close]').forEach(el => el.addEventListener('click', () => {
            modal.classList.remove('show');
            disciplinaModal = null;
        }));
        modal.addEventListener('click', e => {
            if (e.target === modal) { modal.classList.remove('show'); disciplinaModal = null; }
        });
    });

    document.getElementById('form-horario').addEventListener('submit', async e => {
        e.preventDefault();
        try {
            await api(`/ti/disciplinas/${disciplinaModal.id}/horarios/`, {
                method: 'POST',
                corpo: {
                    dia: document.getElementById('h-dia').value,
                    inicio: document.getElementById('h-inicio').value,
                    fim: document.getElementById('h-fim').value
                }
            });
            mostrarToast('Horário adicionado.', 'ok');
            await carregarDisciplinas();
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    });

    document.getElementById('form-matricula').addEventListener('submit', async e => {
        e.preventDefault();
        const alunoId = document.getElementById('m-aluno').value;
        if (!alunoId) return mostrarToast('Selecione um aluno.', 'erro');
        try {
            await api(`/ti/disciplinas/${disciplinaModal.id}/matriculas/`, {
                method: 'POST', corpo: { aluno_id: Number(alunoId) }
            });
            mostrarToast('Aluno matriculado.', 'ok');
            await Promise.all([renderizarMatriculas(), carregarDisciplinas()]);
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    });
}

/* ---- Horários ---- */
function abrirHorarios(d) {
    disciplinaModal = d;
    renderizarHorarios();
    document.getElementById('modal-horarios').classList.add('show');
}

function renderizarHorarios() {
    const d = disciplinaModal;
    document.getElementById('horarios-titulo').textContent = `${d.nome} (${d.codigo})`;
    const alvo = document.getElementById('lista-horarios');
    alvo.innerHTML = d.horarios.length ? d.horarios.map(h => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;font-size:14px;">
            <span>${esc(h.dia_nome)} · ${h.inicio} às ${h.fim}</span>
            <button class="btn btn-light" data-remover="${h.id}">Remover</button>
        </div>`).join('')
        : '<p>Nenhum horário cadastrado.</p>';

    alvo.querySelectorAll('[data-remover]').forEach(btn => btn.addEventListener('click', async () => {
        try {
            await api(`/ti/horarios/${btn.getAttribute('data-remover')}/`, { method: 'DELETE' });
            mostrarToast('Horário removido.', 'ok');
            await carregarDisciplinas();
        } catch (err) {
            mostrarToast(err.message, 'erro');
        }
    }));
}

/* ---- Matrículas ---- */
function abrirMatriculas(d) {
    disciplinaModal = d;
    document.getElementById('matriculas-titulo').textContent = `${d.nome} (${d.codigo})`;
    renderizarMatriculas();
    document.getElementById('modal-matriculas').classList.add('show');
}

async function renderizarMatriculas() {
    try {
        const dados = await api(`/ti/disciplinas/${disciplinaModal.id}/matriculas/`);
        const alvo = document.getElementById('lista-matriculas');
        alvo.innerHTML = dados.matriculas.length ? dados.matriculas.map(m => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;font-size:14px;">
                <span>${esc(m.aluno)} <span style="color:var(--text-muted);">· ${esc(m.matricula)}</span></span>
                <button class="btn btn-light" data-remover="${m.id}" data-nome="${esc(m.aluno)}">Remover</button>
            </div>`).join('')
            : '<p>Nenhum aluno matriculado.</p>';

        document.getElementById('m-aluno').innerHTML = dados.disponiveis.length
            ? dados.disponiveis.map(a => `<option value="${a.id}">${esc(a.nome)} · ${esc(a.matricula)}</option>`).join('')
            : '<option value="">Todos os alunos já estão matriculados</option>';

        alvo.querySelectorAll('[data-remover]').forEach(btn => btn.addEventListener('click', async () => {
            if (!confirm(`Remover ${btn.getAttribute('data-nome')} da disciplina?\nAs notas lançadas para ele nesta disciplina serão perdidas.`)) return;
            try {
                await api(`/ti/matriculas/${btn.getAttribute('data-remover')}/`, { method: 'DELETE' });
                mostrarToast('Matrícula removida.', 'ok');
                await Promise.all([renderizarMatriculas(), carregarDisciplinas()]);
            } catch (err) {
                mostrarToast(err.message, 'erro');
            }
        }));
    } catch (err) {
        mostrarToast(err.message, 'erro');
    }
}
