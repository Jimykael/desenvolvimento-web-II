import customtkinter as ctk


ctk.deactivate_automatic_dpi_awareness()

from tkinter import *
import sqlite3
import os
import re
import hmac
import hashlib
import secrets
from datetime import datetime
from tkinter import messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont


CAMINHO_IMAGEM_CAMPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uneb2.jpeg")
ARQUIVO_USUARIO_LEMBRADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuario_lembrado.txt")

# Conta de TI criada automaticamente na PRIMEIRA execução (quando a tabela Corporativo está vazia).
# É com ela que a equipe de TI entra no sistema para cadastrar alunos e docentes.
# TROQUE a senha abaixo antes de rodar pela primeira vez.
TI_INICIAL = {"nome": "Administrador TI", "usuario": "admin", "email":"ti@acadsystem.com", "senha": "admin123"}


def gera_hash_senha(senha):
    """guarda a senha criptografada (PPBKDF2 + sal aleatório), nunca em texto puro."""
    sal = secrets.token_bytes(16)  # 16 bytes de sal aleatório
    resumo = hashlib.pbkdf2_hmac('sha256', senha.encode("utf-8"), sal, 200_000)
    return sal.hex() + "$" + resumo.hex()


def confere_senha(senha, armazenado):
    """confere a senha digitada com a armazenada no banco (criptografada)"""
    try:
        sal_hex, resumo_hex = armazenado.split("$")
        resumo = hashlib.pbkdf2_hmac('sha256', senha.encode("utf-8"), bytes.fromhex(sal_hex), 200_000)
        return hmac.compare_digest(resumo.hex(), resumo_hex)
    except ValueError:
        return False  # formato inválido, não confere

def carregar_usuario_lembrado():
    """retorna (perfil, usuario) salvos pelo 'lembrar meu usuario' (a senha NUNCA é salva)"""
    try:
        with open(ARQUIVO_USUARIO_LEMBRADO, "r", encoding="utf-8") as f:
            linha = f.read().splitlines()
            if len(linha) == 2:
                return linha[0].strip(), linha[1].strip()
    except OSError:
        pass
    return "" , ""  # perfil, usuario vazios


def salvar_usuario_lembrado(perfil, usuario):
    """salva o perfil e usuário no arquivo de lembrete (a senha NUNCA é salva)"""
    try:
        with open(ARQUIVO_USUARIO_LEMBRADO, "w", encoding="utf-8") as f:
            f.write(f"{perfil}\n{usuario}\n")
    except OSError:
        pass

def esquecer_usuario_lembrado():
    """apaga o arquivo de lembrete, se existir"""
    try:
        os.remove(ARQUIVO_USUARIO_LEMBRADO)
    except OSError:
        pass

def carregar_fonte(tamanho, negrito=False, italico=False, serifada=True):
    """Tenta carregar a fonte mais parecida com o design (Georgia/Segoe UI no Windows),
    com fallback para fontes livres equivalentes caso não estejam disponíveis."""
    if serifada:
        if negrito and italico:
            candidatos = ["georgiaz.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"]
        elif italico:
            candidatos = ["georgiai.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"]
        elif negrito:
            candidatos = ["georgiab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
        else:
            candidatos = ["georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
    else:
        if negrito:
            candidatos = ["segoeuib.ttf", "arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        else:
            candidatos = ["segoeui.ttf", "arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]

    for nome in candidatos:
        try:
            return ImageFont.truetype(nome, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()

# ------------------------------------------------------------------
# PALETA DE CORES
# ------------------------------------------------------------------
COR_PAINEL_ESCURO = "#dbeafe"      # fundo do painel esquerdo 
COR_BRANCO = "#ffffff"             # fundo do painel direito
COR_VERMELHO = "#c81e3a"           # "ACESSO RESTRITO", links
COR_TITULO = "#111827"             # título principal 
COR_SUBTITULO = "#6b7280"          # texto cinza descritivo
COR_BORDA_INPUT = "#d1d5db"        # borda dos campos
COR_BOTAO = "#3F475A"              # botão principal (preto/azulado)
COR_BOTAO_HOVER = "#1f2937"
COR_CAIXA_SEGURANCA = "#f3f4f6"    # caixinha "ambiente seguro"
COR_CINZA_CLARO = "#9ca3af"        # rodapé

#regras de cada perfil: em qual tabela do banco de dados ele esta, e por quais campos pode acessar.
PERFIS = {
    "Portal do Aluno": {
        "tabela": "Alunos", "colunas_login": ["Email"],
        "rotulo": "E-mail institucional",
        "exemplo": "Ex: nome.sobrenome@uneb.br",
        "titulo": "aluno(a)",
    },
    "Portal do Docente": {
        "tabela": "Docentes", "colunas_login": ["Email", "Registro"],
        "rotulo": "E-mail institucional ou nº de registro",
        "exemplo": "Ex: 1234567 ou nome.sobrenome@uneb.br",
        "titulo": "docente",
    },
    "Corporativo / TI": {
        "tabela": "Corporativo", "colunas_login": ["Usuario", "Email"],
        "rotulo": "Usuário ou e-mail corporativo",
        "exemplo": "Ex: admin ou ti@acadsystem.com",
        "titulo": "equipe de TI",
    },
}


# nomes em português para o rodapé de data e hora (não depende do idioma do sistema)
DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# os 8 botões da tela principal de cada perfil (por enquanto são só placeholders,
# exceto "Cadastrar aluno/docente" da TI, que continuam funcionando - veja tela_principal)
BOTOES_PRINCIPAIS = {
    "Portal do Aluno": [
        "Conferir notas e aulas", "Frequência", "Materiais didáticos", "Horários e cronograma",
        "Calendário acadêmico", "Solicitações", "Mensagens", "Meu perfil",
    ],
    "Portal do Docente": [
        "Conferir matérias e alunos", "Lançar notas", "Registrar frequência", "Materiais didáticos",
        "Cronograma de aulas", "Calendário acadêmico", "Mensagens", "Meu perfil",
    ],
    "Corporativo / TI": [
        "Conferir docentes e discentes", "Cadastrar aluno", "Cadastrar docente", "Gerenciar cursos",
        "Relatórios", "Calendário acadêmico", "Suporte técnico", "Configurações",
    ],
}


class BackEnd():
    def conecta_db(self):
        self.conn = sqlite3.connect("sistema_cadastros.db")
        self.cursor = self.conn.cursor()
 
    def desconecta_db(self):
        self.conn.close()
 
    def cria_tabela(self):
        """Uma tabela para cada perfil. (A tabela antiga 'Usuarios', se existir, não é mais usada.)"""
        self.conecta_db()
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Alunos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Nome TEXT NOT NULL,
                Email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                Matricula TEXT NOT NULL UNIQUE,
                Senha TEXT NOT NULL
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Docentes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Nome TEXT NOT NULL,
                Email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                Registro TEXT NOT NULL UNIQUE,
                Senha TEXT NOT NULL
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Corporativo(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Nome TEXT NOT NULL,
                Usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
                Email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                Senha TEXT NOT NULL
                );
            """)
 
            # primeira execução: cria a conta de TI (sem ela ninguém conseguiria cadastrar alunos/docentes)
            self.cursor.execute("SELECT COUNT(*) FROM Corporativo")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute(
                    "INSERT INTO Corporativo(Nome, Usuario, Email, Senha) VALUES(?, ?, ?, ?)",
                    (TI_INICIAL["nome"], TI_INICIAL["usuario"], TI_INICIAL["email"],
                     gera_hash_senha(TI_INICIAL["senha"])))
                print(f"Conta de TI criada: usuário '{TI_INICIAL['usuario']}' (a senha está em TI_INICIAL, no topo do código)")
            self.conn.commit()
        finally:
            self.desconecta_db()
 
    def autentica(self, perfil, identificador, senha):
        """Procura a pessoa na tabela do perfil escolhido. Retorna o nome se o login e a senha
        conferem; senão, None."""
        cfg = PERFIS[perfil]
        condicao = " OR ".join(f"{coluna} = ? COLLATE NOCASE" for coluna in cfg["colunas_login"])
        try:
            self.conecta_db()
            self.cursor.execute(f"SELECT Nome, Senha FROM {cfg['tabela']} WHERE {condicao}",
                                (identificador,) * len(cfg["colunas_login"]))
            linha = self.cursor.fetchone()
        finally:
            self.desconecta_db()
 
        if linha and confere_senha(senha, linha[1]):
            return linha[0]
        return None
 
    def verifica_login(self):
        perfil = self.aba_perfil.get()
        usuario = self.username_login_entry.get().strip()
        senha = self.senha_login_entry.get()
 
        if usuario == "" or senha == "":
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPor favor, preencha todos os campos!")
            return
        if perfil == "Portal do Aluno" and "@" not in usuario:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nO acesso do aluno é feito pelo e-mail institucional!")
            return
 
        try:
            nome = self.autentica(perfil, usuario, senha)
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\n{e}")
            return
 
        if nome is None:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nLogin ou senha incorretos!\nSe ainda não tem acesso, procure o setor de TI.")
            return
 
        if self.lembrar_usuario.get() == 1:
            salvar_usuario_lembrado(perfil, usuario)
        else:
            esquecer_usuario_lembrado()
 
        self.usuario_ti_logado = nome if perfil == "Corporativo / TI" else None
        self.tela_principal(perfil, nome)
 
    def cadastrar_pessoa(self):
        """Cadastra um aluno ou docente. Só funciona com a equipe de TI logada."""
        if not self.usuario_ti_logado:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nSó a equipe de TI pode fazer cadastros.\nEntre pelo Portal Corporativo / TI.")
            self.tela_de_login()
            return
 
        tipo = self.tipo_cadastro
        if tipo == "Aluno":
            tabela, coluna_id, rotulo_id = "Alunos", "Matricula", "essa matrícula"
        else:
            tabela, coluna_id, rotulo_id = "Docentes", "Registro", "esse número de registro"
 
        nome = self.nome_cadastro_entry.get().strip()
        email = self.email_cadastro_entry.get().strip()
        identificador = self.id_cadastro_entry.get().strip()
        senha = self.senha_cadastro_entry.get()
        confirma_senha = self.confirma_senha_entry.get()
 
        if "" in (nome, email, identificador, senha, confirma_senha):
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPreencha todos os campos!")
            return
        elif not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", email):
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nDigite um e-mail válido!\nExemplo: nome.sobrenome@uneb.br")
            return
        elif senha != confirma_senha:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nAs senhas não conferem!")
            return
        elif len(senha) < 6:
            messagebox.showwarning(title="sistema de login", message="ERROR!!!\nA senha deve ter no minimo 6 caracteres!")
            return
 
        try:
            self.conecta_db()
 
            self.cursor.execute(f"SELECT 1 FROM {tabela} WHERE Email = ? COLLATE NOCASE", (email,))
            if self.cursor.fetchone():
                messagebox.showerror(title="sistema de login", message="ERROR!!!\nEste e-mail já está cadastrado!")
                return
 
            self.cursor.execute(f"SELECT 1 FROM {tabela} WHERE {coluna_id} = ?", (identificador,))
            if self.cursor.fetchone():
                messagebox.showerror(title="sistema de login", message=f"ERROR!!!\nJá existe um cadastro com {rotulo_id}!")
                return
 
            self.cursor.execute(
                f"INSERT INTO {tabela}(Nome, Email, {coluna_id}, Senha) VALUES(?, ?, ?, ?)",
                (nome, email, identificador, gera_hash_senha(senha)))
            self.conn.commit()
            messagebox.showinfo(title="sistema de login", message=f"{tipo} {nome} cadastrado(a) com sucesso!")
            self.limpa_entry_cadastro()
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\nErro ao cadastrar!\n{e}")
        finally:
            self.desconecta_db()
 
 
class App(ctk.CTk, BackEnd):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.configuracoes_da_janela_inicial()
        self.usuario_ti_logado = None
        self.cria_tabela()
        self.tela_de_login()
 
    def configuracoes_da_janela_inicial(self):
        self.geometry("950x620")
        self.title("Portal Integrado AcadSystem")
        self.resizable(False, False)
 
    # ----------------------------------------------------------------
    # PAINEL ESQUERDO 
    # ----------------------------------------------------------------
    def cria_painel_esquerdo(self):
        self.para_relogio()   # toda troca de tela passa por aqui: encerra o relógio da tela anterior
        painel = ctk.CTkFrame(self, width=530, height=620, corner_radius=0, fg_color=COR_PAINEL_ESCURO)
        painel.place(x=0, y=0)
        painel.pack_propagate(False)
 
        if False:
            imagem_final = self.montar_imagem_painel_esquerdo()
            self.img_fundo_campus = ImageTk.PhotoImage(imagem_final)  # precisa manter referência
            Label(painel, image=self.img_fundo_campus, bd=0, highlightthickness=0).place(x=0, y=0)
        else:
            # sem a foto: mesmo conteúdo, mas com widgets normais sobre o fundo azul claro
            self.cria_conteudo_painel_esquerdo_sem_foto(painel)
 
        return painel
 
    def montar_imagem_painel_esquerdo(self):
        
        largura_alvo, altura_alvo = 530, 620
        img_original = Image.open(CAMINHO_IMAGEM_CAMPUS).convert("RGB")
 
        # "cover": redimensiona para cobrir a área toda e depois corta o excesso
        escala = max(largura_alvo / img_original.width, altura_alvo / img_original.height)
        nova_largura = round(img_original.width * escala)
        nova_altura = round(img_original.height * escala)
        img_redimensionada = img_original.resize((nova_largura, nova_altura), Image.LANCZOS)
 
        esquerda = (nova_largura - largura_alvo) // 2
        topo_corte = (nova_altura - altura_alvo) // 2
        img_cortada = img_redimensionada.crop((esquerda, topo_corte, esquerda + largura_alvo, topo_corte + altura_alvo))
 
        # escurece a foto para o texto branco ter contraste (efeito "overlay")
        img_final = ImageEnhance.Brightness(img_cortada).enhance(0.38).convert("RGB")
        draw = ImageDraw.Draw(img_final)
 
        # badge/logo
        draw.rounded_rectangle([40, 30, 80, 70], radius=8, fill="#2a2a2a")
        fonte_badge = carregar_fonte(18, negrito=True)
        draw.text((60, 50), "A", font=fonte_badge, fill="white", anchor="mm")
        draw.text((90, 34), "AcadSystem", font=carregar_fonte(16, negrito=True), fill="white")
        draw.text((90, 58), "SISTEMA ACADÊMICO", font=carregar_fonte(10, serifada=False), fill="#e5e7eb")
 
        # barra vermelha + citação
        draw.rectangle([40, 428, 80, 431], fill=COR_VERMELHO)
        draw.text((40, 440), '"Honrar, Servir e Educar."', font=carregar_fonte(24, italico=True), fill="white")
 
        texto_desc = ("Seja bem-vindo ao portal integrado da AcadSystem\n""Aqui você acessa suas notas, frequência, materiais didáticos, cronogramas\n""de pesquisa e serviços administrativos de forma rápida e segura.")
        draw.multiline_text((40, 490), texto_desc, font=carregar_fonte(12, serifada=False),fill="#e5e7eb", spacing=8)
 
        draw.text((40, 592), "© 2026 AcadSystem. Todos os direitos reservados.", font=carregar_fonte(9, serifada=False), fill="#d1d5db")
 
        return img_final
 
    def cria_conteudo_painel_esquerdo_sem_foto(self, painel):
        """Usado apenas se o arquivo de imagem não for encontrado: mesmo conteúdo,
        mas com widgets normais em vez de desenhar na foto."""
        logo = ctk.CTkLabel(painel, text="A", font=("Georgia", 16, "bold"), width=40, height=40,fg_color="#2a2a2a", corner_radius=8,text_color="white")
        logo.place(x=40, y=30)
        ctk.CTkLabel(painel, text="AcadSystem", text_color="#111827", font=("Georgia", 15, "bold"),anchor="w").place(x=90, y=32)
        ctk.CTkLabel(painel, text="SISTEMA ACADÊMICO", text_color="#4b5563",font=("Segoe UI", 9), anchor="w").place(x=90, y=56)
 
        barra = ctk.CTkFrame(painel, width=40, height=3, fg_color=COR_VERMELHO, corner_radius=0)
        barra.place(x=40, y=430)
        ctk.CTkLabel(painel, text='"Honrar, Servir e Educar."', text_color="#111827",font=("Georgia", 22, "italic"), anchor="w", justify="left").place(x=40, y=442)
 
        texto_desc = ("Seja bem-vindo ao portal integrado da AcadSystem\n""Aqui você acessa suas notas, frequência, materiais didáticos, cronogramas\n""de pesquisa e serviços administrativos de forma rápida e segura.")
        ctk.CTkLabel(painel, text=texto_desc, text_color="#374151", font=("Segoe UI", 11),anchor="w", justify="left").place(x=40, y=486)
 
        ctk.CTkLabel(painel, text="© 2026 AcadSystem. Todos os direitos reservados.",text_color="#4b5563", font=("Segoe UI", 8)).place(x=40, y=590)
 
    # ----------------------------------------------------------------
    # TELA DE LOGIN
    # ----------------------------------------------------------------
    def tela_de_login(self):
        self.usuario_ti_logado = None   # ao voltar ao login, a sessão da TI é encerrada
        for widget in self.winfo_children():
            widget.destroy()
 
        self.cria_painel_esquerdo()
 
        painel = ctk.CTkFrame(self, width=420, height=620, corner_radius=0, fg_color=COR_BRANCO)
        painel.place(x=530, y=0)
 
        conteudo = ctk.CTkFrame(painel, fg_color="transparent", width=340)
        conteudo.place(x=40, y=50)
 
        ctk.CTkLabel(conteudo, text="ACESSO RESTRITO", text_color=COR_VERMELHO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(conteudo, text="Portal Integrado AcadSystem", text_color=COR_TITULO,font=("Georgia", 20, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 6))
        ctk.CTkLabel(conteudo, text="Selecione o seu perfil institucional e insira suas\ncredenciais para acessar o sistema acadêmico",text_color=COR_SUBTITULO, font=("Segoe UI", 11), justify="left",anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 20))
 
        # abas de perfil: cada uma entra por uma tabela diferente do banco
        self.aba_perfil = ctk.CTkSegmentedButton(conteudo, values=list(PERFIS.keys()), command=self.muda_perfil, width=340, font=("Segoe UI", 10),fg_color="#e5e7eb", selected_color=COR_BRANCO,selected_hover_color=COR_BRANCO, unselected_hover_color="#e5e7eb",text_color=COR_TITULO, corner_radius=8)
        self.aba_perfil.set("Portal do Aluno")
        self.aba_perfil.grid(row=3, column=0, sticky="w", pady=(0, 20))
 
        padrao = PERFIS["Portal do Aluno"]
        self.lb_campo_usuario = ctk.CTkLabel(conteudo, text=padrao["rotulo"], text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w")
        self.lb_campo_usuario.grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.username_login_entry = ctk.CTkEntry(conteudo, width=340, height=36,placeholder_text=padrao["exemplo"],corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO)
        self.username_login_entry.grid(row=5, column=0, sticky="w", pady=(0, 16))
 
        ctk.CTkLabel(conteudo, text="Senha de Acesso", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=6, column=0, sticky="w", pady=(0, 6))
        self.senha_login_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="Sua senha pessoal",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO, show="*")
        self.senha_login_entry.grid(row=7, column=0, sticky="w", pady=(0, 8))
 
        linha_opcoes = ctk.CTkFrame(conteudo, fg_color="transparent", width=340, height=20)
        linha_opcoes.grid(row=8, column=0, sticky="w", pady=(0, 20))
        linha_opcoes.grid_propagate(False)
        self.lembrar_usuario = ctk.CTkCheckBox(linha_opcoes, text="Lembrar meu usuário", font=("Segoe UI", 10),text_color=COR_SUBTITULO, checkbox_width=16, checkbox_height=16)
        self.lembrar_usuario.place(x=0, y=0)
        self.btn_esqueceu_senha = ctk.CTkLabel(linha_opcoes, text="Esqueceu sua senha?", text_color=COR_VERMELHO,font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_esqueceu_senha.place(x=225, y=1)
        self.btn_esqueceu_senha.bind("<Button-1>", lambda e: self.aviso_esqueceu_senha())
 
        self.btn_login = ctk.CTkButton(conteudo, width=340, height=40, text="Acessar Minha Conta",font=("Segoe UI", 12, "bold"), corner_radius=8,fg_color=COR_BOTAO, hover_color=COR_BOTAO_HOVER,command=self.verifica_login)
        self.btn_login.grid(row=9, column=0, sticky="w", pady=(0, 16))
 
        caixa = ctk.CTkFrame(conteudo, width=340, height=44, fg_color=COR_CAIXA_SEGURANCA, corner_radius=8)
        caixa.grid(row=10, column=0, sticky="w", pady=(0, 16))
        ctk.CTkLabel(caixa, text="🔒  Ambiente seguro. Seus dados de acesso estão protegidos por criptografia.",text_color=COR_SUBTITULO, font=("Segoe UI", 9), wraplength=310, justify="left").place(x=10, y=8)
 
        separador = ctk.CTkFrame(conteudo, width=340, height=1, fg_color=COR_BORDA_INPUT)
        separador.grid(row=11, column=0, sticky="w", pady=(0, 12))
 
        linha_rodape = ctk.CTkFrame(conteudo, fg_color="transparent", width=340, height=20)
        linha_rodape.grid(row=12, column=0, sticky="w")
        ctk.CTkLabel(linha_rodape, text="Primeiro acesso? ", text_color=COR_SUBTITULO,font=("Segoe UI", 10)).grid(row=0, column=0)
        self.btn_primeiro_acesso = ctk.CTkLabel(linha_rodape, text="Fale com o suporte de TI", text_color=COR_VERMELHO,font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_primeiro_acesso.grid(row=0, column=1)
        self.btn_primeiro_acesso.bind("<Button-1>", lambda e: self.aviso_primeiro_acesso())
 
        # "Lembrar meu usuário": volta já na aba certa, com o usuário preenchido e marcado
        perfil_lembrado, usuario_lembrado = carregar_usuario_lembrado()
        if perfil_lembrado in PERFIS and usuario_lembrado:
            self.aba_perfil.set(perfil_lembrado)
            self.muda_perfil(perfil_lembrado)
            self.username_login_entry.insert(0, usuario_lembrado)
            self.lembrar_usuario.select()
 
    # ----------------------------------------------------------------
    # AÇÕES DOS BOTÕES DO LOGIN
    # ----------------------------------------------------------------
    def muda_perfil(self, perfil):
        """Aba de perfil: troca o rótulo e o exemplo do campo de usuário."""
        self.lb_campo_usuario.configure(text=PERFIS[perfil]["rotulo"])
        self.username_login_entry.configure(placeholder_text=PERFIS[perfil]["exemplo"])
 
    def aviso_esqueceu_senha(self):
        messagebox.showinfo(title="redefinir senha", message="Para redefinir a sua senha,\nprocure o setor de TI da instituição.")
 
    def aviso_primeiro_acesso(self):
        messagebox.showinfo(title="primeiro acesso", message="O acesso de alunos e docentes é criado pelo setor de TI.\nProcure o suporte da instituição para receber o seu acesso.")
 
    # ----------------------------------------------------------------
    # TELA PRINCIPAL (depois do login)
    # ----------------------------------------------------------------
    def tela_principal(self, perfil, nome):
        for widget in self.winfo_children():
            widget.destroy()

        self.cria_painel_esquerdo()

        painel = ctk.CTkFrame(self, width=420, height=620, corner_radius=0, fg_color=COR_BRANCO)
        painel.place(x=530, y=0)

        conteudo = ctk.CTkFrame(painel, fg_color="transparent", width=340)
        conteudo.place(x=40, y=30)

        ctk.CTkLabel(conteudo, text="ACESSO AUTORIZADO", text_color=COR_VERMELHO,
                     font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(conteudo, text=f"Olá, {nome}!", text_color=COR_TITULO, font=("Georgia", 24, "bold"),
                     anchor="w", justify="left", wraplength=340).grid(row=1, column=0, sticky="w", pady=(4, 6))
        ctk.CTkLabel(conteudo, text=f"Você entrou no AcadSystem como {PERFIS[perfil]['titulo']}.",
                     text_color=COR_SUBTITULO, font=("Segoe UI", 11),
                     anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 16))

        estilo_botao = dict(width=340, height=36, font=("Segoe UI", 12, "bold"), corner_radius=8,
                            fg_color=COR_BOTAO, hover_color=COR_BOTAO_HOVER)
        estilo_sair = dict(width=340, height=32, font=("Segoe UI", 10), corner_radius=8, fg_color="transparent",
                           hover_color="#f3f4f6", text_color=COR_VERMELHO, border_width=1, border_color=COR_VERMELHO)

        # botões que já têm função de verdade (os demais são placeholders)
        acoes_reais = {}
        if perfil == "Corporativo / TI":
            acoes_reais = {
                "Cadastrar aluno": lambda: self.tela_de_cadastro("Aluno"),
                "Cadastrar docente": lambda: self.tela_de_cadastro("Docente"),
            }

        for i, texto in enumerate(BOTOES_PRINCIPAIS[perfil]):
            comando = acoes_reais.get(texto) or (lambda t=texto: self.botao_em_breve(t))
            ctk.CTkButton(conteudo, text=texto, command=comando,
                          **estilo_botao).grid(row=3 + i, column=0, sticky="w", pady=(0, 8))

        ctk.CTkButton(conteudo, text="Sair da conta", command=self.tela_de_login,
                      **estilo_sair).grid(row=11, column=0, sticky="w", pady=(10, 0))

        # rodapé: data e hora (atualiza sozinho a cada segundo)
        ctk.CTkFrame(painel, width=340, height=1, fg_color=COR_BORDA_INPUT).place(x=40, y=570)
        self.lb_data_hora = ctk.CTkLabel(painel, text="", text_color=COR_SUBTITULO, font=("Segoe UI", 9))
        self.lb_data_hora.place(x=40, y=582)
        self.atualiza_data_hora()

    def botao_em_breve(self, nome_botao):
        """Ação provisória dos botões que ainda não foram implementados."""
        messagebox.showinfo(title="AcadSystem", message=f"\"{nome_botao}\"\nEsta função ainda está em desenvolvimento.")

    def atualiza_data_hora(self):
        agora = datetime.now()
        dia_semana = DIAS_SEMANA[agora.weekday()].capitalize()
        self.lb_data_hora.configure(
            text=f"{dia_semana}, {agora.day} de {MESES[agora.month - 1]} de {agora.year}   •   {agora:%H:%M:%S}")
        self.id_relogio = self.after(1000, self.atualiza_data_hora)

    def para_relogio(self):
        """Cancela a atualização do rodapé (chamado ao sair da tela principal)."""
        if getattr(self, "id_relogio", None):
            try:
                self.after_cancel(self.id_relogio)
            except Exception:
                pass
            self.id_relogio = None

    # ----------------------------------------------------------------
    # TELA DE CADASTRO (só alcançável pela equipe de TI logada)
    # ----------------------------------------------------------------
    def tela_de_cadastro(self, tipo):
        if not self.usuario_ti_logado:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nSó a equipe de TI pode fazer cadastros.\nEntre pelo Portal Corporativo / TI.")
            self.tela_de_login()
            return
 
        self.tipo_cadastro = tipo
        for widget in self.winfo_children():
            widget.destroy()
 
        self.cria_painel_esquerdo()
 
        painel = ctk.CTkFrame(self, width=420, height=620, corner_radius=0, fg_color=COR_BRANCO)
        painel.place(x=530, y=0)
 
        conteudo = ctk.CTkFrame(painel, fg_color="transparent", width=340)
        conteudo.place(x=40, y=30)
 
        if tipo == "Aluno":
            rotulo_id, exemplo_id = "Matrícula", "Ex: 202610293"
            dica = "O aluno entrará com o e-mail institucional\ne a senha inicial definida aqui."
        else:
            rotulo_id, exemplo_id = "Número de registro", "Ex: 1234567"
            dica = "O docente entrará com o e-mail ou o número\nde registro e a senha inicial definida aqui."
 
        ctk.CTkLabel(conteudo, text="CADASTRO PELA EQUIPE DE TI", text_color=COR_VERMELHO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(conteudo, text=f"Cadastrar {tipo.lower()}", text_color=COR_TITULO,font=("Georgia", 24, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 6))
        ctk.CTkLabel(conteudo, text=dica, text_color=COR_SUBTITULO, font=("Segoe UI", 11), justify="left",anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 10))
 
        def campo(linha, rotulo, placeholder, senha=False):
            ctk.CTkLabel(conteudo, text=rotulo, text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=linha, column=0, sticky="w", pady=(0, 4))
            entrada = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text=placeholder,corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO, show="*" if senha else "")
            entrada.grid(row=linha + 1, column=0, sticky="w", pady=(0, 6))
            return entrada
 
        self.nome_cadastro_entry = campo(3, "Nome completo", "Nome e sobrenome")
        self.email_cadastro_entry = campo(5, "E-mail institucional", "nome.sobrenome@uneb.br")
        self.id_cadastro_entry = campo(7, rotulo_id, exemplo_id)
        self.senha_cadastro_entry = campo(9, "Senha inicial", "Mínimo de 6 caracteres", senha=True)
        self.confirma_senha_entry = campo(11, "Confirmar senha", "Repita a senha", senha=True)
 
        self.btn_cadastrar_user = ctk.CTkButton(conteudo, width=340, height=40, text=f"Cadastrar {tipo.lower()}",font=("Segoe UI", 12, "bold"), corner_radius=8,fg_color=COR_BOTAO, hover_color=COR_BOTAO_HOVER,command=self.cadastrar_pessoa)
        self.btn_cadastrar_user.grid(row=13, column=0, sticky="w", pady=(8, 12))
 
        self.btn_voltar_painel = ctk.CTkButton(conteudo, width=340, height=32, text="Voltar ao painel da TI",font=("Segoe UI", 10), corner_radius=8, fg_color="transparent",hover_color="#f3f4f6", text_color=COR_VERMELHO, border_width=1,border_color=COR_VERMELHO, command=lambda: self.tela_principal("Corporativo / TI", self.usuario_ti_logado))
        self.btn_voltar_painel.grid(row=14, column=0, sticky="w")
 
    def limpa_entry_cadastro(self):
        for entrada in (self.nome_cadastro_entry, self.email_cadastro_entry, self.id_cadastro_entry,
                        self.senha_cadastro_entry, self.confirma_senha_entry):
            entrada.delete(0, ctk.END)
 
    def limpa_entry_login(self):
        self.username_login_entry.delete(0, ctk.END)
        self.senha_login_entry.delete(0, ctk.END)
 
 
if __name__ == "__main__":
    app = App()
    app.mainloop()
 