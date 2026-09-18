import customtkinter as ctk
import tkinter
import sqlite3


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
            CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            confirma_senha TEXT NOT NULL
            );
        """)
        self.conn.commit()
        print("Tabela criada com sucesso!")
        self.desconecta_db()
        
    def cadastrar_usuario(self):
        self.username_cadastro = self.username_cadastro_entry.get()
        self.email_cadastro = self.email_cadastro_entry.get()
        self.senha_cadastro = self.senha_cadastro_entry.get()
        self.confirma_senha = self.confirma_senha_entry.get()

        self.cursor.execute("""
            INSERT INTO usuarios(username, email, senha, confirma_senha)
        """)



class App(ctk.CTk, BackEnd):
    def __init__(self):
        super().__init__()
        self.configuracoes_da_janela_inicial()
        self.tela_de_login()

    #configurando a janela principal
    def configuracoes_da_janela_inicial(self):
        self.geometry("700x400") 
        self.title("Login")
        self.resizable(False, False) 

    def tela_de_login(self):  
        #remover a tela de cadastro
        self.tela_de_cadastro.place_forget()

        #trabalhando com as imagens
        self.img = tkinter.PhotoImage(file="login/assets/uneb.png") # Substitua pelo caminho da imagem
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

        self.username_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Seu nome de usuario",font=("Century Gothic bold", 16), corner_radius=15, border_color="blue") 
        self.username_login_entry.grid(row=1, column=0, pady=10, padx=10)

        self.senha_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Sua senha...", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*")
        self.senha_login_entry.grid(row=2, column=0, pady=10, padx=10)

        self.ver_senha = ctk.CTkCheckBox(self.frame_login,text="clique para ver a senha", font=("Century Gothic bold", 14),corner_radius=20)
        self.ver_senha.grid(row=3, column=0, pady=10, padx=10)

        self.btn_login = ctk.CTkButton(self.frame_login, width=300,text="Fazer Login".upper(), font=("Century Gothic bold", 16), corner_radius=15)
        self.btn_login.grid(row=4, column=0, pady=10, padx=10)

        self.span = ctk.CTkLabel(self.frame_login, text="Se não tiver conta,\n clique no botão abaixo para se cadastrar", font=("Century Gothic bold", 10))
        self.span.grid(row=5, column=0, pady=10, padx=10)

        self.btn_cadastrar = ctk.CTkButton(self.frame_login, width=300,fg_color="green",hover_color="darkgreen",text="Fazer Cadastro".upper(), font=("Century Gothic bold", 16), corner_radius=15, command=self.tela_de_cadastro)
        self.btn_cadastrar.grid(row=6, column=0, pady=10, padx=10)


def tela_de_cadastro(self):
        #remover o frame de login
        self.frame_login.place_forget()

        #criar o frame do formulario de cadastro
        self.frame_cadastro = ctk.CTkFrame(self, width=350, height=380)
        self.frame_cadastro.place(x=350, y=10)

        #criando o titulo da tela de cadastro
        self.lb_img = ctk.CTkLabel(self, text=None, image=self.img)
        self.lb_img.grid(row=0, column=0, padx=10)

        #cria os widgets do frame de cadastro
        self.username_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Seu nome de usuario",font=("Century Gothic bold", 16), corner_radius=15, border_color="blue") 
        self.username_cadastro_entry.grid(row=1, column=0, pady=5, padx=10)

        self.email_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Email do usuario",font=("Century Gothic bold", 16), corner_radius=15, border_color="blue") 
        self.email_cadastro_entry.grid(row=2, column=0, pady=5, padx=10)
        
        self.senha_cadastro_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="senha do usuario", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*")
        self.senha_cadastro_entry.grid(row=3, column=0, pady=5, padx=10)

        self.confirma_senha_entry = ctk.CTkEntry(self.frame_cadastro, width=300, placeholder_text="Confirme sua senha",font=("Century Gothic bold", 16), corner_radius=15, border_color="blue", show="*") 
        self.confirma_senha_entry.grid(row=4, column=0, pady=5, padx=10)

        self.ver_senha = ctk.CTkCheckBox(self.frame_cadastro,text="clique para ver a senha", font=("Century Gothic bold", 14),corner_radius=20)
        self.ver_senha.grid(row=5, column=0, pady=5, padx=10)

        self.btn_cadastrar_user = ctk.CTkButton(self.frame_cadastro, width=300,fg_color="green",hover_color="darkgreen",text="Fazer Cadastro".upper(), font=("Century Gothic bold", 16), corner_radius=15, command=self.cadastrar_usuario)
        self.btn_cadastrar_user.grid(row=6, column=0, pady=5, padx=10)

        self.btn_login_back = ctk.CTkButton(self.frame_login, width=300,text="voltar a Login".upper(), font=("Century Gothic bold", 16), corner_radius=15,fg_color="#444", hover_color="#333", command=self.tela_de_login)
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