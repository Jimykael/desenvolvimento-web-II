/* =====================================================
   AcadSystem — Lógica do Portal do Professor
   Dados carregados da API (/api/docente/...)
   ===================================================== */

let turmas = [];          // turmas do docente
let turmaDiario = null;   // id da turma aberta no modal
let alunosDiario = [];    // alunos da turma aberta no modal

document.addEventListener('DOMContentLoaded', () => {
    inicializarPortal('docente', 'Você não possui novos avisos.');

    configurarModal();
    configurarSalvamentos();
    document.getElementById('sel-turma-notas').addEventListener('change', e => carregarNotas(e.target.value));
    document.getElementById('sel-turma-plano').addEventListener('change', e => carregarPlano(e.target.value));
    carregarPainel();
});

async function carregarPainel(inicial = true) {
    try {
        const dados = await api('/docente/painel/');
        turmas = dados.turmas;
        document.getElementById('st-turmas').textContent = dados.resumo.turmas;
        document.getElementById('st-alunos').textContent = dados.resumo.alunos;
        document.getElementById('st-aulas').textContent = dados.resumo.aulas_lancadas;
        document.getElementById('st-pendentes').textContent = dados.resumo.notas_pendentes;
        renderizarTurmas();
        if (inicial) preencherSeletores(); // nas atualizações, mantém a turma selecionada
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

/* ---------- Lista de turmas ---------- */
function renderizarTurmas() {
    const alvo = document.getElementById('lista-turmas');
    if (!turmas.length) {
        alvo.innerHTML = '<p class="page-sub">Você ainda não possui turmas atribuídas. Procure a secretaria/TI.</p>';
        return;
    }
    alvo.innerHTML = turmas.map(t => `
        <div class="list-row">
            <div>
                <span class="tag" style="background:var(--emerald-bg);color:var(--emerald);">${esc(t.curso)}</span>
                <h5>${esc(t.nome)} (${esc(t.codigo)})</h5>
                <p>${esc(t.dias || 'Sem horário')}${t.horario ? ' · ' + esc(t.horario) : ''} · ${t.alunos} alunos matriculados</p>
            </div>
            <button class="btn btn-dark" data-turma="${t.id}">Abrir Diário</button>
        </div>`).join('');

    alvo.querySelectorAll('button[data-turma]').forEach(btn => {
        btn.addEventListener('click', () => abrirDiario(Number(btn.getAttribute('data-turma'))));
    });
}

function preencherSeletores() {
    const opcoes = turmas.length
        ? turmas.map(t => `<option value="${t.id}">${esc(t.nome)} (${esc(t.codigo)})</option>`).join('')
        : '<option value="">Nenhuma turma</option>';
    document.querySelectorAll('.sel-turma').forEach(sel => { sel.innerHTML = opcoes; });
    if (turmas.length) {
        carregarNotas(turmas[0].id);
        carregarPlano(turmas[0].id);
    }
}

/* ---------- Modal do diário de classe ---------- */
function dataHoje() {
    const d = new Date();
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const dia = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mes}-${dia}`;
}

function configurarModal() {
    const modal = document.getElementById('modal-diario');

    modal.querySelectorAll('[data-close]').forEach(el => {
        el.addEventListener('click', () => modal.classList.remove('show'));
    });
    modal.addEventListener('click', e => {
        if (e.target === modal) modal.classList.remove('show');
    });

    document.getElementById('salvar-presenca').addEventListener('click', async () => {
        const presencas = [...document.querySelectorAll('#lista-presenca input[data-aluno]')].map(chk => ({
            aluno_id: Number(chk.getAttribute('data-aluno')),
            presente: chk.checked
        }));
        try {
            const r = await api(`/docente/turmas/${turmaDiario}/frequencia/`, {
                method: 'POST',
                corpo: { data: document.getElementById('data-aula').value, presencas }
            });
            modal.classList.remove('show');
            mostrarToast(`Frequência registrada: ${r.presentes}/${r.total} presentes.`, 'ok');
            carregarPainel(false);
        } catch (e) {
            mostrarToast(e.message, 'erro');
        }
    });
}

async function abrirDiario(turmaId) {
    try {
        const dados = await api(`/docente/turmas/${turmaId}/alunos/`);
        turmaDiario = turmaId;
        alunosDiario = dados.alunos;
        document.getElementById('modal-turma-nome').textContent = `${dados.turma.nome} (${dados.turma.codigo})`;
        const data = document.getElementById('data-aula');
        data.value = dataHoje();
        data.max = dataHoje();

        document.getElementById('lista-presenca').innerHTML = alunosDiario.length
            ? alunosDiario.map(a => `
                <label style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;cursor:pointer;">
                    <input type="checkbox" checked data-aluno="${a.id}">
                    <span style="font-size:14px;">${esc(a.nome)} <span style="color:var(--text-muted);">· ${esc(a.matricula)}</span></span>
                </label>`).join('')
            : '<p>Nenhum aluno matriculado nesta turma.</p>';
        document.getElementById('modal-diario').classList.add('show');
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

/* ---------- Lançamento de notas ---------- */
async function carregarNotas(turmaId) {
    const tbody = document.querySelector('#tabela-lancamento tbody');
    if (!turmaId) { tbody.innerHTML = ''; return; }
    try {
        const dados = await api(`/docente/turmas/${turmaId}/alunos/`);
        tbody.innerHTML = dados.alunos.length ? dados.alunos.map(a => `
            <tr data-aluno="${a.id}">
                <td>${esc(a.matricula)}</td><td>${esc(a.nome)}</td>
                <td><input class="nota" type="number" min="0" max="10" step="0.1" value="${a.n1 ?? ''}"></td>
                <td><input class="nota" type="number" min="0" max="10" step="0.1" value="${a.n2 ?? ''}"></td>
                <td class="media">—</td>
            </tr>`).join('')
            : '<tr><td colspan="5">Nenhum aluno matriculado nesta turma.</td></tr>';
        configurarCalculoMedias();
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

/* Cálculo automático de médias enquanto o professor digita */
function configurarCalculoMedias() {
    const calcular = tr => {
        const notas = tr.querySelectorAll('.nota');
        const n1 = parseFloat(notas[0].value);
        const n2 = parseFloat(notas[1].value);
        const celula = tr.querySelector('.media');
        if (!isNaN(n1) && !isNaN(n2)) {
            const media = (n1 + n2) / 2;
            celula.innerHTML = `<span class="pill ${media >= 6 ? 'pill-green' : 'pill-red'}">${media.toFixed(1).replace('.', ',')}</span>`;
        } else {
            celula.textContent = '—';
        }
    };
    document.querySelectorAll('#tabela-lancamento tr[data-aluno]').forEach(tr => {
        tr.querySelectorAll('.nota').forEach(input => input.addEventListener('input', () => calcular(tr)));
        calcular(tr);
    });
}

/* ---------- Plano de ensino ---------- */
async function carregarPlano(turmaId) {
    if (!turmaId) return;
    try {
        const p = await api(`/docente/turmas/${turmaId}/plano/`);
        document.getElementById('plano-ementa').value = p.ementa;
        document.getElementById('plano-carga').value = p.carga_horaria;
        document.getElementById('plano-bibliografia').value = p.bibliografia;
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

/* ---------- Botões de salvar ---------- */
function configurarSalvamentos() {
    document.getElementById('salvar-notas').addEventListener('click', async () => {
        const turmaId = document.getElementById('sel-turma-notas').value;
        const notas = [...document.querySelectorAll('#tabela-lancamento tr[data-aluno]')].map(tr => {
            const campos = tr.querySelectorAll('.nota');
            return { aluno_id: Number(tr.getAttribute('data-aluno')), n1: campos[0].value, n2: campos[1].value };
        });
        if (!turmaId || !notas.length) return mostrarToast('Não há notas para salvar.', 'erro');
        try {
            await api(`/docente/turmas/${turmaId}/notas/`, { method: 'POST', corpo: { notas } });
            mostrarToast('Notas salvas com sucesso!', 'ok');
            carregarPainel(false);
        } catch (e) {
            mostrarToast(e.message, 'erro');
        }
    });

    document.getElementById('salvar-plano').addEventListener('click', async () => {
        const turmaId = document.getElementById('sel-turma-plano').value;
        if (!turmaId) return mostrarToast('Selecione uma turma.', 'erro');
        try {
            await api(`/docente/turmas/${turmaId}/plano/`, {
                method: 'PUT',
                corpo: {
                    ementa: document.getElementById('plano-ementa').value,
                    carga_horaria: document.getElementById('plano-carga').value,
                    bibliografia: document.getElementById('plano-bibliografia').value
                }
            });
            mostrarToast('Plano de ensino atualizado.', 'ok');
        } catch (e) {
            mostrarToast(e.message, 'erro');
        }
    });
}
