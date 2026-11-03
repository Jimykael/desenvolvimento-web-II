/* =====================================================
   AcadSystem — Lógica do Portal do Aluno
   Dados carregados da API (/api/aluno/painel/)
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Inicialização comum (sessão, navegação, logout, sino, relógio)
    inicializarPortal('aluno', 'Você não possui novos avisos institucionais.');

    configurarBuscaNotas();
    configurarAcoesRapidas();
    configurarDocumentos();
    carregarPainel();
});

async function carregarPainel() {
    try {
        const dados = await api('/aluno/painel/');
        renderizarResumo(dados.resumo);
        renderizarBoletim(dados.boletim);
        renderizarFrequencia(dados.frequencias);
        renderizarHorario(dados.horarios);
    } catch (e) {
        mostrarToast(e.message, 'erro');
    }
}

function renderizarResumo(r) {
    document.getElementById('st-cr').textContent = fmtNum(r.cr);
    document.getElementById('st-freq').textContent = fmtNum(r.frequencia_geral, '%');
    document.getElementById('st-disc').textContent = r.disciplinas;
    document.getElementById('st-carga').textContent = `2026.1 · ${r.carga_horaria}h totais`;
    document.getElementById('st-rematricula').textContent = r.rematricula;

    const hint = document.getElementById('st-freq-hint');
    if (r.frequencia_geral === null) hint.textContent = 'Nenhuma aula registrada ainda';
    else hint.textContent = r.frequencia_geral >= 75 ? 'Situação regular' : 'Abaixo do mínimo (75%)';
}

function renderizarBoletim(boletim) {
    const tbody = document.querySelector('#tabela-notas tbody');
    if (!boletim.length) {
        tbody.innerHTML = '<tr><td colspan="7">Você ainda não está matriculado em nenhuma disciplina.</td></tr>';
        return;
    }
    tbody.innerHTML = boletim.map(b => `
        <tr>
            <td>${esc(b.disciplina)}</td>
            <td>${esc(b.codigo)}</td>
            <td>${fmtNum(b.n1)}</td>
            <td>${fmtNum(b.n2)}</td>
            <td>${fmtNum(b.media)}</td>
            <td>${fmtNum(b.frequencia, '%')}</td>
            <td><span class="pill ${esc(b.situacao.classe)}">${esc(b.situacao.rotulo)}</span></td>
        </tr>`).join('');
}

/* Renderiza a lista de frequência com barras de progresso */
function renderizarFrequencia(lista) {
    const alvo = document.getElementById('lista-frequencia');
    if (!lista.length) {
        alvo.innerHTML = '<p class="page-sub">Nenhuma disciplina encontrada.</p>';
        return;
    }
    alvo.innerHTML = lista.map(f => {
        const pct = f.percentual;
        const cor = pct === null ? 'var(--text-muted)'
            : pct >= 85 ? 'var(--emerald)' : pct >= 75 ? '#B45309' : 'var(--red)';
        return `
            <div style="margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px;">
                    <span style="font-weight:600;">${esc(f.disciplina)}</span>
                    <span style="font-weight:600;color:${cor};">${pct === null ? 'Sem aulas registradas' : fmtNum(pct, '%')}</span>
                </div>
                <div class="progress"><span style="width:${pct || 0}%;background:${cor};"></span></div>
            </div>`;
    }).join('');
}

/* Monta a grade semanal (linhas = faixas de horário, colunas = Seg..Sex) */
function renderizarHorario(horarios) {
    const tbody = document.querySelector('#tabela-horario tbody');
    if (!horarios.length) {
        tbody.innerHTML = '<tr><td colspan="6">Nenhum horário cadastrado para suas disciplinas.</td></tr>';
        return;
    }
    const faixas = [...new Set(horarios.map(h => `${h.inicio}–${h.fim}`))].sort();
    tbody.innerHTML = faixas.map(faixa => {
        const colunas = [0, 1, 2, 3, 4].map(dia => {
            const item = horarios.find(h => h.dia === dia && `${h.inicio}–${h.fim}` === faixa);
            return `<td>${item ? esc(item.disciplina) : '—'}</td>`;
        }).join('');
        return `<tr><td>${esc(faixa)}</td>${colunas}</tr>`;
    }).join('');
}

/* Filtra a tabela de notas conforme o texto digitado */
function configurarBuscaNotas() {
    const busca = document.getElementById('busca-notas');
    if (!busca) return;
    busca.addEventListener('input', () => {
        const termo = busca.value.toLowerCase();
        document.querySelectorAll('#tabela-notas tbody tr').forEach(tr => {
            const texto = tr.textContent.toLowerCase();
            tr.classList.toggle('hidden-row', !texto.includes(termo));
        });
    });
}

/* Botões de ação rápida: emitir documento ou ir para outra seção */
function configurarAcoesRapidas() {
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const doc = btn.getAttribute('data-doc');
            const ir = btn.getAttribute('data-ir');
            if (ir) {
                const item = document.querySelector(`.nav-item[data-target="${ir}"]`);
                if (item) trocarSecao(ir, item);
            } else if (doc) {
                emitirDocumento(doc);
            }
        });
    });
}

/* Botões "Emitir PDF" na seção Documentos */
function configurarDocumentos() {
    document.querySelectorAll('button[data-doc]').forEach(btn => {
        btn.addEventListener('click', () => emitirDocumento(btn.getAttribute('data-doc')));
    });
}

/* Emissão de documentos ainda não implementada no backend */
function emitirDocumento(nome) {
    mostrarToast(`A emissão de "${nome}" ainda não está disponível.`, 'info');
}
