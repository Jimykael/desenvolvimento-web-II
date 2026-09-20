import customtkinter as ctk
from tkinter import *
import sqlite3
from tkinter import messagebox




class BackEnd():
    def conecta_db(self):
        self.conn = sqlite3.connect("sistema_cadastros.db")
        self.cursor = self.conn.cursor()
        print("banco de dados conectado com sucesso!")

    def desconecta_db(self):
        self.conn.close()
        print("banco de dados desconectado com sucesso!")

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
        print("Tabela criada com sucesso!")
        self.desconecta_db()

    def cadastrar_usuario(self):
        self.username_cadastro = self.username_cadastro_entry.get()
        self.email_cadastro = self.email_cadastro_entry.get()
        self.senha_cadastro = self.senha_cadastro_entry.get()
        self.confirma_senha_cadastro = self.confirma_senha_entry.get()

        if (self.username_cadastro == "" or self.email_cadastro == "" or
                self.senha_cadastro == "" or self.confirma_senha_cadastro == ""):
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPreencha todos os campos!")
            return
        elif len(self.username_cadastro) < 4:
            messagebox.showwarning(title="sistema de login", message="ERROR!!!\n O nome de usuario deve ter no minimo 4 caracteres!")
            return
        elif self.senha_cadastro != self.confirma_senha_cadastro:
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nAs senhas não conferem!")
            return
        elif len(self.senha_cadastro) < 6:
            messagebox.showwarning(title="sistema de login", message="ERROR!!!\nA senha deve ter no minimo 6 caracteres!")
            return

        # Só chega aqui se passou em todas as validações
        try:
            self.conecta_db()
            self.cursor.execute("""
                INSERT INTO Usuarios(Username, Email, Senha, Confirma_Senha)
                VALUES(?, ?, ?, ?)""",
                (self.username_cadastro, self.email_cadastro, self.senha_cadastro, self.confirma_senha_cadastro))
            self.conn.commit()
            messagebox.showinfo(title="sistema de login", message=f"Usuario {self.username_cadastro} cadastrado com sucesso!")
            self.limpa_entry_cadastro()
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\nErro ao cadastrar usuario!\n{e}")
        finally:
            self.desconecta_db()

    def verifica_login(self):
        self.username_login = self.username_login_entry.get()
        self.senha_login = self.senha_login_entry.get()

        if self.username_login == "" or self.senha_login == "":
            messagebox.showerror(title="sistema de login", message="ERROR!!!\nPor favor, preencha todos os campos!")
            return

        try:
            self.conecta_db()
            self.cursor.execute(
                """SELECT * FROM Usuarios WHERE (Username = ? AND Senha = ?)""",
                (self.username_login, self.senha_login))
            self.verifica_dados = self.cursor.fetchone()

            if self.verifica_dados:
                messagebox.showinfo(title="sistema de login", message=f"Usuario {self.username_login} \nlogado com sucesso!")
                self.limpa_entry_login()
            else:
                messagebox.showerror(title="sistema de login", message="ERROR!!!\n Usuario ou senha incorretos!\n por favor verifique os seus dados ou cadastre-se!")
        except Exception as e:
            messagebox.showerror(title="sistema de login", message=f"ERROR!!!\n{e}")
        finally:
            self.desconecta_db()



class App(ctk.CTk, BackEnd):
    def __init__(self):
        super().__init__()
        self.configuracoes_da_janela_inicial()
        self.cria_tabela()
        self.tela_de_login()

    #configurando a janela principal
    def configuracoes_da_janela_inicial(self):
        self.geometry("700x400")
        self.title("Login")
        self.resizable(False, False)

    def tela_de_login(self):
        #remover a tela de cadastro
        try:
            self.frame_cadastro.place_forget()
        except AttributeError:
            pass

        #trabalhando com as imagens (só carrega a imagem uma vez)
        if not hasattr(self, "img"):
            self.img = PhotoImage(file=r"C:\Users\Usuário\Documents\GitHub\desenvolvimento-web-II\login\uneb1.png")

        self.lb_img = ctk.CTkLabel(self, text=None, image=self.img)
        self.lb_img.grid(row=0, column=0, padx=10)

        #titulo da nossa plataforma
        self.title = ctk.CTkLabel(self, text="faça seu login ou \n cadastre-se", font=("Century Gothic bold", 14))
        self.title.grid(row=1, column=0, pady=10)

        #Criar frame do formulário de login
        self.frame_login = ctk.CTkFrame(self, width=350, height=380)
        self.frame_login.place(x=350, y=10)

        #colocando widgets dentro do frame - formulario de login
        self.lb_title = ctk.CTkLabel(self.frame_login, text="faça o seu login", font=("Century Gothic bold", 22))
        self.lb_title.grid(row=0, column=0, pady=10, padx=10)

        self.username_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Seu nome de usuario", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue")
        self.username_login_entry.grid(row=1, column=0, pady=10, padx=10)

        self.senha_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Sua senha...", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*")
        self.senha_login_entry.grid(row=2, column=0, pady=10, padx=10)

        self.ver_senha = ctk.CTkCheckBox(self.frame_login, text="clique para ver a senha", font=("Century Gothic bold", 14), corner_radius=20)
        self.ver_senha.grid(row=3, column=0, pady=10, padx=10)

        self.btn_login = ctk.CTkButton(self.frame_login, width=300, text="Fazer Login".upper(), font=("Century Gothic bold", 16), corner_radius=15, command=self.verifica_login)
        self.btn_login.grid(row=4, column=0, pady=10, padx=10)

        self.span = ctk.CTkLabel(self.frame_login, text="Se não tiver conta,\n clique no botão abaixo para se cadastrar", font=("Century Gothic bold", 10))
        self.span.grid(row=5, column=0, pady=10, padx=10)

        self.btn_cadastrar = ctk.CTkButton(self.frame_login, width=300, fg_color="green", hover_color="darkgreen", text="Fazer Cadastro".upper(), font=("Century Gothic bold", 16), corner_radius=15, command=self.tela_de_cadastro)
        self.btn_cadastrar.grid(row=6, column=0, pady=10, padx=10)


    def tela_de_cadastro(self):
        #remover o frame de login
        self.frame_login.place_forget()

        #criar o frame do formulario de cadastro
        self.frame_cadastro = ctk.CTkFrame(self, width=350, height=380)
        self.frame_cadastro.place(x=350, y=10)

        #cria os widgets do frame de cadastro
        self.username_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Seu nome de usuario", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue")
        self.username_cadastro_entry.grid(row=1, column=0, pady=5, padx=10)

        self.email_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Email do usuario", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue")
        self.email_cadastro_entry.grid(row=2, column=0, pady=5, padx=10)

        self.senha_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="senha do usuario", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*")
        self.senha_cadastro_entry.grid(row=3, column=0, pady=5, padx=10)

        self.confirma_senha_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Confirme sua senha", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*")
        self.confirma_senha_entry.grid(row=4, column=0, pady=5, padx=10)

        self.ver_senha_cadastro = ctk.CTkCheckBox(self.frame_cadastro, text="clique para ver a senha", font=("Century Gothic bold", 14), corner_radius=20)
        self.ver_senha_cadastro.grid(row=5, column=0, pady=5, padx=10)

        self.btn_cadastrar_user = ctk.CTkButton(self.frame_cadastro, width=300, fg_color="green", hover_color="darkgreen", text="Fazer Cadastro".upper(), font=("Century Gothic bold", 16), corner_radius=15, command=self.cadastrar_usuario)
        self.btn_cadastrar_user.grid(row=6, column=0, pady=5, padx=10)

        self.btn_login_back = ctk.CTkButton(self.frame_cadastro, width=300, text="voltar a Login".upper(), font=("Century Gothic bold", 16), corner_radius=15, fg_color="#444", hover_color="#333", command=self.tela_de_login)
        self.btn_login_back.grid(row=7, column=0, pady=10, padx=10)


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