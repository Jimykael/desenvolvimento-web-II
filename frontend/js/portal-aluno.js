/* =====================================================
   AcadSystem — Lógica do Portal do Aluno
   ===================================================== */

// Dados de frequência (renderizados via JS com barra de progresso)
const FREQUENCIA = [
    { disc: 'Cálculo Diferencial e Integral I', pct: 95 },
    { disc: 'Algoritmos e Estrutura de Dados I', pct: 90 },
    { disc: 'Introdução à Engenharia', pct: 88 },
    { disc: 'Física Geral I', pct: 82 },
    { disc: 'Metodologia Científica', pct: 100 }
];

document.addEventListener('DOMContentLoaded', () => {
    // Inicialização comum (sessão, navegação, logout, sino, relógio)
    inicializarPortal('aluno', 'Você possui 2 novos avisos institucionais.');

    renderizarFrequencia();
    configurarBuscaNotas();
    configurarAcoesRapidas();
    configurarDocumentos();
});

/* Renderiza a lista de frequência com barras de progresso */
function renderizarFrequencia() {
    const alvo = document.getElementById('lista-frequencia');
    if (!alvo) return;
    alvo.innerHTML = FREQUENCIA.map(f => {
        const cor = f.pct >= 85 ? 'var(--emerald)' : f.pct >= 75 ? '#B45309' : 'var(--red)';
        return `
            <div style="margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px;">
                    <span style="font-weight:600;">${f.disc}</span>
                    <span style="font-weight:600;color:${cor};">${f.pct}%</span>
                </div>
                <div class="progress"><span style="width:${f.pct}%;background:${cor};"></span></div>
            </div>`;
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

function emitirDocumento(nome) {
    mostrarToast(`Gerando "${nome}"... o arquivo estará disponível em instantes.`, 'ok');
}
