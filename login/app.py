import customtkinter as ctk


ctk.deactivate_automatic_dpi_awareness()

from tkinter import *
import sqlite3
import os
from tkinter import messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont


CAMINHO_IMAGEM_CAMPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uneb2.jpeg")


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
COR_PAINEL_ESCURO = "#161616"      # fundo do painel esquerdo 
COR_BRANCO = "#ffffff"             # fundo do painel direito
COR_VERMELHO = "#c81e3a"           # "ACESSO RESTRITO", links
COR_TITULO = "#111827"             # título principal 
COR_SUBTITULO = "#6b7280"          # texto cinza descritivo
COR_BORDA_INPUT = "#d1d5db"        # borda dos campos
COR_BOTAO = "#111827"              # botão principal (preto/azulado)
COR_BOTAO_HOVER = "#1f2937"
COR_CAIXA_SEGURANCA = "#f3f4f6"    # caixinha "ambiente seguro"
COR_CINZA_CLARO = "#9ca3af"        # rodapé


class BackEnd():
    def conecta_db(self):
        self.conn = sqlite3.connect("sistema_cadastros.db")
        self.cursor = self.conn.cursor()

    def desconecta_db(self):
        self.conn.close()

    def cria_tabela(self):
        self.conecta_db()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL,
            Email TEXT NOT NULL,
            Senha TEXT NOT NULL,
            Confirma_Senha TEXT NOT NULL
            );
        """)
        self.conn.commit()
        self.desconecta_db()

    def cadastrar_usuario(self):
        username = self.username_cadastro_entry.get()
        email = self.email_cadastro_entry.get()
        senha = self.senha_cadastro_entry.get()
        confirma_senha = self.confirma_senha_entry.get()

        if username == "" or email == "" or senha == "" or confirma_senha == "":
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPreencha todos os campos!")
            return
        elif len(username) < 4:
            messagebox.showwarning(title="sistema de login", message="ERROR!!!\nO nome de usuario deve ter no minimo 4 caracteres!")
            return
        elif senha != confirma_senha:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nAs senhas não conferem!")
            return
        elif len(senha) < 6:
            messagebox.showwarning(title="sistema de login", message="ERROR!!!\nA senha deve ter no minimo 6 caracteres!")
            return

        try:
            self.conecta_db()
            self.cursor.execute("""
                INSERT INTO Usuarios(Username, Email, Senha, Confirma_Senha)
                VALUES(?, ?, ?, ?)""", (username, email, senha, confirma_senha))
            self.conn.commit()
            messagebox.showinfo(title="sistema de login", message=f"Usuario {username} cadastrado com sucesso!")
            self.limpa_entry_cadastro()
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\nErro ao cadastrar usuario!\n{e}")
        finally:
            self.desconecta_db()

    def verifica_login(self):
        username = self.username_login_entry.get()
        senha = self.senha_login_entry.get()

        if username == "" or senha == "":
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPor favor, preencha todos os campos!")
            return

        try:
            self.conecta_db()
            self.cursor.execute(
                """SELECT * FROM Usuarios WHERE (Username = ? AND Senha = ?)""",
                (username, senha))
            dados = self.cursor.fetchone()

            if dados:
                messagebox.showinfo(title="sistema de login", message=f"Usuario {username}\nlogado com sucesso!")
                self.limpa_entry_login()
            else:
                messagebox.showerror(title="sistema de login", message="ERROR!!!\nUsuario ou senha incorretos!\npor favor verifique os seus dados ou cadastre-se!")
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\n{e}")
        finally:
            self.desconecta_db()


class App(ctk.CTk, BackEnd):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.configuracoes_da_janela_inicial()
        self.cria_tabela()
        self.tela_de_login()

    def configuracoes_da_janela_inicial(self):
        self.geometry("950x620")
        self.title("Portal Integrado UNEB")
        self.resizable(False, False)

    # ----------------------------------------------------------------
    # PAINEL ESQUERDO 
    # ----------------------------------------------------------------
    def cria_painel_esquerdo(self):
        painel = ctk.CTkFrame(self, width=530, height=620, corner_radius=0, fg_color=COR_PAINEL_ESCURO)
        painel.place(x=0, y=0)
        painel.pack_propagate(False)

        if os.path.isfile(CAMINHO_IMAGEM_CAMPUS):
            imagem_final = self.montar_imagem_painel_esquerdo()
            self.img_fundo_campus = ImageTk.PhotoImage(imagem_final)  # precisa manter referência
            Label(painel, image=self.img_fundo_campus, bd=0, highlightthickness=0).place(x=0, y=0)
        else:
            # sem a foto: mesmo conteúdo, mas com widgets normais sobre o fundo escuro sólido
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
        draw.text((60, 50), "U", font=fonte_badge, fill="white", anchor="mm")
        draw.text((90, 34), "UNEB", font=carregar_fonte(16, negrito=True), fill="white")
        draw.text((90, 58), "UNIVERSIDADE DO ESTADO DA BAHIA",font=carregar_fonte(10, serifada=False), fill="#e5e7eb")

        # barra vermelha + citação
        draw.rectangle([40, 428, 80, 431], fill=COR_VERMELHO)
        draw.text((40, 440), '"Honrar, Servir e Educar."', font=carregar_fonte(24, italico=True), fill="white")

        texto_desc = ("Seja bem-vindo ao portal integrado da UNEB - Universidade do Estado da Bahia.\n""Aqui você acessa suas notas, frequência, materiais didáticos, cronogramas\n""de pesquisa e serviços administrativos de forma rápida e segura.")
        draw.multiline_text((40, 490), texto_desc, font=carregar_fonte(12, serifada=False),fill="#e5e7eb", spacing=8)

        draw.text((40, 592), "© 2026 UNEB - Universidade do Estado da Bahia. Todos os direitos reservados.",font=carregar_fonte(9, serifada=False), fill="#d1d5db")

        return img_final

    def cria_conteudo_painel_esquerdo_sem_foto(self, painel):
        """Usado apenas se o arquivo de imagem não for encontrado: mesmo conteúdo,
        mas com widgets normais em vez de desenhar na foto."""
        logo = ctk.CTkLabel(painel, text="U", font=("Georgia", 16, "bold"), width=40, height=40,fg_color="#2a2a2a", corner_radius=8)
        logo.place(x=40, y=30)
        ctk.CTkLabel(painel, text="UNEB", text_color="white", font=("Georgia", 15, "bold"),anchor="w").place(x=90, y=32)
        ctk.CTkLabel(painel, text="UNIVERSIDADE DO ESTADO DA BAHIA", text_color="#9ca3af",font=("Segoe UI", 9), anchor="w").place(x=90, y=56)

        barra = ctk.CTkFrame(painel, width=40, height=3, fg_color=COR_VERMELHO, corner_radius=0)
        barra.place(x=40, y=430)
        ctk.CTkLabel(painel, text='"Honrar, Servir e Educar."', text_color="white",font=("Georgia", 22, "italic"), anchor="w", justify="left").place(x=40, y=442)

        texto_desc = ("Seja bem-vindo ao portal integrado da UNEB - Universidade do Estado da Bahia.\n""Aqui você acessa suas notas, frequência, materiais didáticos, cronogramas\n""de pesquisa e serviços administrativos de forma rápida e segura.")
        ctk.CTkLabel(painel, text=texto_desc, text_color="#d1d5db", font=("Segoe UI", 11),anchor="w", justify="left").place(x=40, y=486)

        ctk.CTkLabel(painel, text="© 2026 UNEB - Universidade do Estado da Bahia. Todos os direitos reservados.",text_color="#6b7280", font=("Segoe UI", 8)).place(x=40, y=590)

    # ----------------------------------------------------------------
    # TELA DE LOGIN
    # ----------------------------------------------------------------
    def tela_de_login(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.cria_painel_esquerdo()

        painel = ctk.CTkFrame(self, width=420, height=620, corner_radius=0, fg_color=COR_BRANCO)
        painel.place(x=530, y=0)

        conteudo = ctk.CTkFrame(painel, fg_color="transparent", width=340)
        conteudo.place(x=40, y=50)

        ctk.CTkLabel(conteudo, text="ACESSO RESTRITO", text_color=COR_VERMELHO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(conteudo, text="Portal Integrado UNEB", text_color=COR_TITULO,font=("Georgia", 24, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 6))
        ctk.CTkLabel(conteudo, text="Selecione o seu perfil institucional e insira suas\ncredenciais para acessar o sistema acadêmico da UNEB.",text_color=COR_SUBTITULO, font=("Segoe UI", 11), justify="left",anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 20))

        # abas de perfil
        self.aba_perfil = ctk.CTkSegmentedButton(conteudo, values=["Portal do Aluno", "Portal do Docente", "Corporativo / TI"],width=340, font=("Segoe UI", 10),fg_color="#e5e7eb", selected_color=COR_BRANCO,selected_hover_color=COR_BRANCO, unselected_hover_color="#e5e7eb",text_color=COR_TITULO, corner_radius=8)
        self.aba_perfil.set("Portal do Aluno")
        self.aba_perfil.grid(row=3, column=0, sticky="w", pady=(0, 20))

        ctk.CTkLabel(conteudo, text="Matrícula, CPF ou E-mail institucional", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.username_login_entry = ctk.CTkEntry(conteudo, width=340, height=36,placeholder_text="Ex: 202610293 ou nome.sobrenome@uneb.br",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO)
        self.username_login_entry.grid(row=5, column=0, sticky="w", pady=(0, 16))

        ctk.CTkLabel(conteudo, text="Senha de Acesso", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=6, column=0, sticky="w", pady=(0, 6))
        self.senha_login_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="Sua senha pessoal",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO, show="*")
        self.senha_login_entry.grid(row=7, column=0, sticky="w", pady=(0, 8))

        linha_opcoes = ctk.CTkFrame(conteudo, fg_color="transparent", width=340, height=20)
        linha_opcoes.grid(row=8, column=0, sticky="w", pady=(0, 20))
        linha_opcoes.grid_propagate(False)
        self.lembrar_usuario = ctk.CTkCheckBox(linha_opcoes, text="Lembrar meu usuário", font=("Segoe UI", 10),text_color=COR_SUBTITULO, checkbox_width=16, checkbox_height=16)
        self.lembrar_usuario.place(x=0, y=0)
        ctk.CTkLabel(linha_opcoes, text="Esqueceu sua senha?", text_color=COR_VERMELHO,font=("Segoe UI", 10, "bold"), cursor="hand2").place(x=225, y=1)

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
        self.btn_ir_cadastro = ctk.CTkLabel(linha_rodape, text="Ative seu usuário", text_color=COR_VERMELHO,font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_ir_cadastro.grid(row=0, column=1)
        self.btn_ir_cadastro.bind("<Button-1>", lambda e: self.tela_de_cadastro())

    # ----------------------------------------------------------------
    # TELA DE CADASTRO (mesma linguagem visual, campos de registro)
    # ----------------------------------------------------------------
    def tela_de_cadastro(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.cria_painel_esquerdo()

        painel = ctk.CTkFrame(self, width=420, height=620, corner_radius=0, fg_color=COR_BRANCO)
        painel.place(x=530, y=0)

        conteudo = ctk.CTkFrame(painel, fg_color="transparent", width=340)
        conteudo.place(x=40, y=50)

        ctk.CTkLabel(conteudo, text="PRIMEIRO ACESSO", text_color=COR_VERMELHO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(conteudo, text="Criar Cadastro", text_color=COR_TITULO,font=("Georgia", 24, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 6))
        ctk.CTkLabel(conteudo, text="Preencha seus dados para ativar seu acesso\nao sistema acadêmico da UNEB.",text_color=COR_SUBTITULO, font=("Segoe UI", 11), justify="left",anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 24))

        ctk.CTkLabel(conteudo, text="Nome de usuário", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.username_cadastro_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="Seu nome de usuário",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO)
        self.username_cadastro_entry.grid(row=4, column=0, sticky="w", pady=(0, 14))

        ctk.CTkLabel(conteudo, text="E-mail institucional", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=5, column=0, sticky="w", pady=(0, 6))
        self.email_cadastro_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="nome.sobrenome@uneb.br",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO)
        self.email_cadastro_entry.grid(row=6, column=0, sticky="w", pady=(0, 14))

        ctk.CTkLabel(conteudo, text="Senha", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=7, column=0, sticky="w", pady=(0, 6))
        self.senha_cadastro_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="Mínimo de 6 caracteres",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO, show="*")
        self.senha_cadastro_entry.grid(row=8, column=0, sticky="w", pady=(0, 14))

        ctk.CTkLabel(conteudo, text="Confirmar senha", text_color=COR_TITULO,font=("Segoe UI", 11, "bold"), anchor="w").grid(row=9, column=0, sticky="w", pady=(0, 6))
        self.confirma_senha_entry = ctk.CTkEntry(conteudo, width=340, height=36, placeholder_text="Repita a senha",corner_radius=8, border_color=COR_BORDA_INPUT, border_width=1,fg_color=COR_BRANCO, text_color=COR_TITULO, show="*")
        self.confirma_senha_entry.grid(row=10, column=0, sticky="w", pady=(0, 22))

        self.btn_cadastrar_user = ctk.CTkButton(conteudo, width=340, height=40, text="Criar minha conta",font=("Segoe UI", 12, "bold"), corner_radius=8,fg_color=COR_BOTAO, hover_color=COR_BOTAO_HOVER,command=self.cadastrar_usuario)
        self.btn_cadastrar_user.grid(row=11, column=0, sticky="w", pady=(0, 16))

        self.btn_voltar_login = ctk.CTkButton(conteudo, width=340, height=32, text="Já tenho conta, voltar ao login",font=("Segoe UI", 10), corner_radius=8, fg_color="transparent",hover_color="#f3f4f6", text_color=COR_VERMELHO, border_width=1,border_color=COR_VERMELHO, command=self.tela_de_login)
        self.btn_voltar_login.grid(row=12, column=0, sticky="w")

    def limpa_entry_cadastro(self):
        self.username_cadastro_entry.delete(0, ctk.END)
        self.email_cadastro_entry.delete(0, ctk.END)
        self.senha_cadastro_entry.delete(0, ctk.END)
        self.confirma_senha_entry.delete(0, ctk.END)

    def limpa_entry_login(self):
        self.username_login_entry.delete(0, ctk.END)
        self.senha_login_entry.delete(0, ctk.END)


if __name__ == "__main__":
    app = App()
    app.mainloop()