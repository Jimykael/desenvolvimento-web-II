/* =====================================================
   AcadSystem — Lógica do Portal do Professor
   ===================================================== */

// Alunos de exemplo para a chamada do diário de classe
const ALUNOS_TURMA = [
    { mat: '202610293', nome: 'Maria Clara Souza' },
    { mat: '202610118', nome: 'João Pedro Alves' },
    { mat: '202610457', nome: 'Ana Beatriz Costa' },
    { mat: '202610802', nome: 'Lucas Fernandes Dias' },
    { mat: '202610990', nome: 'Carla Ribeiro Nunes' }
];

document.addEventListener('DOMContentLoaded', () => {
    inicializarPortal('docente', 'Você tem 12 notas pendentes de lançamento.');

    configurarDiario();
    configurarCalculoMedias();
    configurarSalvamentos();
});

/* ---------- Modal do diário de classe ---------- */
function configurarDiario() {
    const modal = document.getElementById('modal-diario');

    document.querySelectorAll('button[data-turma]').forEach(btn => {
        btn.addEventListener('click', () => abrirDiario(btn.getAttribute('data-turma')));
    });

    modal.querySelectorAll('[data-close]').forEach(el => {
        el.addEventListener('click', () => modal.classList.remove('show'));
    });
    modal.addEventListener('click', e => {
        if (e.target === modal) modal.classList.remove('show');
    });

    document.getElementById('salvar-presenca').addEventListener('click', () => {
        const total = ALUNOS_TURMA.length;
        const presentes = document.querySelectorAll('#lista-presenca input:checked').length;
        modal.classList.remove('show');
        mostrarToast(`Frequência registrada: ${presentes}/${total} presentes.`, 'ok');
    });
}

function abrirDiario(turma) {
    document.getElementById('modal-turma-nome').textContent = turma;
    const lista = document.getElementById('lista-presenca');
    lista.innerHTML = ALUNOS_TURMA.map(a => `
        <label style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;cursor:pointer;">
            <input type="checkbox" checked>
            <span style="font-size:14px;">${a.nome} <span style="color:var(--text-muted);">· ${a.mat}</span></span>
        </label>`).join('');
    document.getElementById('modal-diario').classList.add('show');
}

/* ---------- Cálculo automático de médias ---------- */
function configurarCalculoMedias() {
    const tabela = document.getElementById('tabela-lancamento');
    if (!tabela) return;

    const calcular = tr => {
        const notas = tr.querySelectorAll('.nota');
        const n1 = parseFloat(notas[0].value);
        const n2 = parseFloat(notas[1].value);
        const celula = tr.querySelector('.media');
        if (!isNaN(n1) && !isNaN(n2)) {
            const media = (n1 + n2) / 2;
            celula.textContent = media.toFixed(1);
            celula.innerHTML = `<span class="pill ${media >= 6 ? 'pill-green' : 'pill-red'}">${media.toFixed(1)}</span>`;
        } else {
            celula.textContent = '—';
        }
    };

    tabela.querySelectorAll('tr[data-aluno]').forEach(tr => {
        tr.querySelectorAll('.nota').forEach(input => {
            input.addEventListener('input', () => calcular(tr));
        });
    });
}

/* ---------- Botões de salvar ---------- */
function configurarSalvamentos() {
    const salvarNotas = document.getElementById('salvar-notas');
    if (salvarNotas) salvarNotas.addEventListener('click', () => mostrarToast('Notas salvas com sucesso!', 'ok'));

    const salvarPlano = document.getElementById('salvar-plano');
    if (salvarPlano) salvarPlano.addEventListener('click', () => mostrarToast('Plano de ensino atualizado.', 'ok'));
}
