import tkinter as tk
from tkinter import messagebox
import pandas as pd 
import os
import sys
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk


import customtkinter
from app_state import AppState

from backend import (
    carregar_dados, verificar_login, inicializar_banco_de_dados, DATABASE_NAME, CSV_FILE_NAME,
    USUARIOS_FUNCIONARIOS, USUARIOS_GERENTES,
    COL_CATEGORIA, COL_NOME_PRODUTO, COL_VALOR,
    COL_SENTIMENTO, COL_PRECO, resource_path_backend
)
from gui.dashboard_tabs_ui import DashboardTabsUIManager

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class DashboardApp(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_state = AppState()

        self.title("Dashboard de Análise de Vendas - Tkinter")
        self.geometry("1400x950")

        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        self.font_normal = ("Arial", 12)
        self.font_bold = ("Arial", 12, "bold")
        self.font_title = ("Arial", 18, "bold")
        self.font_header = ("Arial", 14, "bold")
        self.font_metric_label = ("Arial", 11)
        self.font_metric_value = ("Arial", 16, "bold")

        self._container = customtkinter.CTkFrame(self, fg_color="transparent")
        self._container.pack(side="top", fill="both", expand=True)

        self.login_frame = None
        self.dashboard_frame = None
        self.tabs_ui_manager = None

        self.show_login_page()
        self.protocol("WM_DELETE_WINDOW", self._on_app_closing)

    def clear_container(self):
        for widget in self._container.winfo_children():
            widget.destroy()

    def show_login_page(self):
        self.clear_container()
        self.login_frame = customtkinter.CTkFrame(self._container, fg_color="transparent")
        self.login_frame.pack(expand=True)

        logo_path_gui = resource_path("SLA.png")
        try:
            if os.path.exists(logo_path_gui):
                img = Image.open(logo_path_gui)
                img.thumbnail((200, 200))
                self.login_logo_image = ImageTk.PhotoImage(img)
                logo_label = customtkinter.CTkLabel(self.login_frame, image=self.login_logo_image, text="")
                logo_label.pack(pady=(0, 10))
            else:
                print(f"DEBUG: Logo não encontrado em {logo_path_gui}")
                customtkinter.CTkLabel(self.login_frame, text=f"Logo não encontrado", font=self.font_normal).pack(pady=(0, 10))
        except Exception as e:
            print(f"DEBUG: Erro ao carregar logo: {e}")
            customtkinter.CTkLabel(self.login_frame, text=f"Erro ao carregar logo: {e}", font=self.font_normal).pack(pady=(0, 10))

        customtkinter.CTkLabel(self.login_frame, text="Bem-vindo ao Dashboard de Vendas", font=self.font_title).pack(pady=(0,10))
        customtkinter.CTkLabel(self.login_frame, text="Login", font=self.font_header).pack(pady=(0,20))

        form_frame = customtkinter.CTkFrame(self.login_frame)
        form_frame.pack()

        customtkinter.CTkLabel(form_frame, text="Usuário:", font=self.font_normal).grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.username_entry = customtkinter.CTkEntry(form_frame, width=250, font=self.font_normal)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        self.username_entry.focus()

        customtkinter.CTkLabel(form_frame, text="Senha:", font=self.font_normal).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.password_entry = customtkinter.CTkEntry(form_frame, show="*", width=250, font=self.font_normal)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        login_button = customtkinter.CTkButton(form_frame, text="Entrar", command=self._attempt_login, font=self.font_bold)
        login_button.grid(row=2, column=0, columnspan=2, pady=20)
        self.bind('<Return>', lambda event: self._attempt_login())

    def _attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = verificar_login(username, password)

        if role:
            self.app_state.logged_in = True
            self.app_state.user_role = role
            self.app_state.username = username
            if role == "funcionario" and username in USUARIOS_FUNCIONARIOS:
                self.app_state.user_permissions = USUARIOS_FUNCIONARIOS[username]
            else:
                self.app_state.user_permissions = {}

            self.app_state.df_vendas = carregar_dados()
            if self.app_state.df_vendas is None:
                messagebox.showerror("Erro de Dados", "Não foi possível carregar os dados de vendas. O dashboard pode não funcionar corretamente.")
                self.app_state.df_vendas = pd.DataFrame()
            elif self.app_state.df_vendas.empty:
                messagebox.showwarning("Dados Vazios", "Os dados de vendas estão vazios. O dashboard pode não apresentar informações.")
            self.app_state.df_filtrado = self.app_state.df_vendas.copy() if self.app_state.df_vendas is not None else pd.DataFrame()

            self.show_dashboard_page()
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos, ou conta inativa.")
            self.password_entry.delete(0, "end")

    def _logout(self):
        self.app_state = AppState()
        self.show_login_page()

    def _on_app_closing(self):
        self.destroy()

    def show_dashboard_page(self):
        self.clear_container()
        self.dashboard_frame = customtkinter.CTkFrame(self._container, fg_color="transparent")
        self.dashboard_frame.pack(fill="both", expand=True)

        self.sidebar_frame = customtkinter.CTkFrame(self.dashboard_frame, width=280)
        self.sidebar_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.sidebar_frame.pack_propagate(False)

        self.main_content_area = customtkinter.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.main_content_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self._build_sidebar_content()
        self._build_main_dashboard_content()
        self._apply_filters()

    def _build_sidebar_content(self):
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        logo_path_gui = resource_path("SLA.png")
        try:
            if os.path.exists(logo_path_gui):
                img = Image.open(logo_path_gui)
                img.thumbnail((200, 200))
                self.logo_image = ImageTk.PhotoImage(img)
                logo_label = customtkinter.CTkLabel(self.sidebar_frame, image=self.logo_image, text="")
                logo_label.pack(pady=10)
            else:
                print(f"DEBUG: Logo não encontrado em {logo_path_gui}")
                customtkinter.CTkLabel(self.sidebar_frame, text=f"Logo não encontrado", font=self.font_normal).pack(pady=10)
        except Exception as e:
            print(f"DEBUG: Erro ao carregar logo: {e}")
            customtkinter.CTkLabel(self.sidebar_frame, text=f"Erro ao carregar logo: {e}", font=self.font_normal).pack(pady=10)

        logout_button = customtkinter.CTkButton(self.sidebar_frame, text="Logout", command=self._logout, font=self.font_bold)
        logout_button.pack(pady=10, fill="x")

        customtkinter.CTkLabel(self.sidebar_frame, text=f"Usuário: {self.app_state.username}", font=self.font_normal, anchor="w").pack(fill="x", padx=10)
        customtkinter.CTkLabel(self.sidebar_frame, text=f"Perfil: {self.app_state.user_role.capitalize()}", font=self.font_normal, anchor="w").pack(fill="x", padx=10)
        customtkinter.CTkFrame(self.sidebar_frame, height=2, fg_color="gray").pack(fill="x", pady=10, padx=10)

        customtkinter.CTkLabel(self.sidebar_frame, text="Filtros do Dashboard", font=self.font_header, anchor="w").pack(pady=(10,5), fill="x", padx=10)
        
        customtkinter.CTkLabel(self.sidebar_frame, text=f"Selecione a {COL_CATEGORIA}:", font=self.font_normal, anchor="w").pack(fill="x", padx=10)
        self.categoria_var = tk.StringVar(value="Todas")
        categorias_disponiveis = ["Todas"]
        if self.app_state.df_vendas is not None and COL_CATEGORIA in self.app_state.df_vendas.columns:
            categorias_unicas = self.app_state.df_vendas[COL_CATEGORIA].dropna().unique()
            categorias_disponiveis.extend(sorted(list(categorias_unicas)))

        self.categoria_combobox = customtkinter.CTkComboBox(self.sidebar_frame, variable=self.categoria_var, values=categorias_disponiveis, state="readonly", command=self._apply_filters_ctk_combobox_fix, font=self.font_normal)
        self.categoria_combobox.pack(fill="x", pady=5, padx=10)

        if self.app_state.user_role == "gerente":
            customtkinter.CTkFrame(self.sidebar_frame, height=2, fg_color="gray").pack(fill="x", pady=10, padx=10)
            customtkinter.CTkLabel(self.sidebar_frame, text="Painel do Gerente", font=self.font_header, anchor="w").pack(pady=(10,5), fill="x", padx=10)
            self._build_manager_panel()

    def _build_manager_panel(self):
        customtkinter.CTkLabel(self.sidebar_frame, text="Criar Nova Conta de Funcionário", font=self.font_bold).pack(anchor="w", padx=10, pady=(5,0))
        create_user_lf = customtkinter.CTkFrame(self.sidebar_frame) 
        create_user_lf.pack(fill="x", pady=5, padx=10)

        customtkinter.CTkLabel(create_user_lf, text="Nome de Usuário:", font=self.font_normal).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.new_username_entry = customtkinter.CTkEntry(create_user_lf, font=self.font_normal)
        self.new_username_entry.grid(row=0, column=1, sticky="ew", pady=2)

        customtkinter.CTkLabel(create_user_lf, text="Senha:", font=self.font_normal).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.new_password_entry = customtkinter.CTkEntry(create_user_lf, show="*", font=self.font_normal)
        self.new_password_entry.grid(row=1, column=1, sticky="ew", pady=2)

        customtkinter.CTkLabel(create_user_lf, text="Confirmar Senha:", font=self.font_normal).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.new_password_confirm_entry = customtkinter.CTkEntry(create_user_lf, show="*", font=self.font_normal)
        self.new_password_confirm_entry.grid(row=2, column=1, sticky="ew", pady=2)

        self.new_can_see_details_var = tk.BooleanVar(value=False)
        customtkinter.CTkCheckBox(create_user_lf, text="Permitir ver dados detalhados", variable=self.new_can_see_details_var, font=self.font_normal).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.new_is_active_var = tk.BooleanVar(value=True)
        customtkinter.CTkCheckBox(create_user_lf, text="Conta Ativa", variable=self.new_is_active_var, font=self.font_normal).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        customtkinter.CTkButton(create_user_lf, text="Criar Conta", command=self._create_employee_account, font=self.font_bold).grid(row=5, column=0, columnspan=2, pady=10)

        customtkinter.CTkLabel(self.sidebar_frame, text="Gerenciar Funcionários Ativos", font=self.font_bold).pack(anchor="w", padx=10, pady=(10,0))
        self.manage_employees_scroll_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame, height=200)
        self.manage_employees_scroll_frame.pack(fill="x", pady=5, padx=10, expand=True)
        self._populate_manage_employees_panel()

    def _populate_manage_employees_panel(self):
        for widget in self.manage_employees_scroll_frame.winfo_children():
            widget.destroy()

        if not USUARIOS_FUNCIONARIOS:
            customtkinter.CTkLabel(self.manage_employees_scroll_frame, text="Nenhum funcionário cadastrado.", font=self.font_normal).pack(pady=5)
            return

        for user, data in USUARIOS_FUNCIONARIOS.items():
            user_frame = customtkinter.CTkFrame(self.manage_employees_scroll_frame)
            user_frame.pack(fill="x", expand=True)
            customtkinter.CTkLabel(user_frame, text=f"Usuário: {user}", font=self.font_bold).pack(anchor="w", padx=5)

            is_active_var = tk.BooleanVar(value=data.get("active", False))
            active_cb = customtkinter.CTkCheckBox(user_frame, text="Ativo", variable=is_active_var,
                                        command=lambda u=user, var=is_active_var: self._update_employee_status(u, "active", var.get()), font=self.font_normal)
            active_cb.pack(anchor="w", padx=5)

            can_see_details_var = tk.BooleanVar(value=data.get("can_see_details", False))
            details_cb = customtkinter.CTkCheckBox(user_frame, text="Ver dados detalhados", variable=can_see_details_var,
                                         command=lambda u=user, var=can_see_details_var: self._update_employee_status(u, "can_see_details", var.get()), font=self.font_normal)
            details_cb.pack(anchor="w", padx=5)
            customtkinter.CTkFrame(user_frame, height=1, fg_color="gray").pack(fill="x", pady=3, padx=5)

    def _create_employee_account(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        confirm_password = self.new_password_confirm_entry.get()
        can_see_details = self.new_can_see_details_var.get()
        is_active = self.new_is_active_var.get()

        if not username or not password:
            messagebox.showerror("Erro", "Nome de usuário e senha são obrigatórios.")
            return
        if password != confirm_password:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
        if username in USUARIOS_FUNCIONARIOS or username in USUARIOS_GERENTES:
            messagebox.showerror("Erro", "Nome de usuário já existe.")
            return

        USUARIOS_FUNCIONARIOS[username] = {
            "password": password,
            "can_see_details": can_see_details,
            "active": is_active
        }
        messagebox.showinfo("Sucesso", f"Conta para '{username}' criada com sucesso!")
        self.new_username_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.new_password_confirm_entry.delete(0, "end")
        self.new_can_see_details_var.set(False)
        self.new_is_active_var.set(True)
        self._populate_manage_employees_panel()

    def _update_employee_status(self, username, key, value):
        if username in USUARIOS_FUNCIONARIOS:
            USUARIOS_FUNCIONARIOS[username][key] = value
            messagebox.showinfo("Sucesso", f"Status de '{username}' atualizado.")
            self._populate_manage_employees_panel()
    def _apply_filters_ctk_combobox_fix(self, choice=None):
        self._apply_filters()

    def _apply_filters(self, event=None):
        if self.app_state.df_vendas is None or self.app_state.df_vendas.empty:
            self.app_state.df_filtrado = pd.DataFrame()
            self._update_dashboard_content()
            return

        df_temp = self.app_state.df_vendas.copy()
        categoria_selecionada = self.categoria_var.get()

        if categoria_selecionada != "Todas" and COL_CATEGORIA in df_temp.columns:
            df_temp = df_temp[df_temp[COL_CATEGORIA] == categoria_selecionada]

        self.app_state.df_filtrado = df_temp
        self._update_dashboard_content()

    def _build_main_dashboard_content(self):
        for widget in self.main_content_area.winfo_children():
            widget.destroy()

        customtkinter.CTkLabel(self.main_content_area, text="Dashboard de Análise de Vendas", font=self.font_title).pack(pady=(0,10), anchor="w")
        customtkinter.CTkFrame(self.main_content_area, height=2, fg_color="gray").pack(fill="x", pady=(0,10))

        self.indicators_frame = customtkinter.CTkFrame(self.main_content_area, fg_color="transparent")
        self.indicators_frame.pack(fill="x", pady=10)
        self._build_indicators()

        self.notebook = customtkinter.CTkTabview(self.main_content_area)
        self.notebook.pack(expand=True, fill="both", pady=10)
        
        self.tabs_ui_manager = DashboardTabsUIManager(self, self.notebook)
        self.tabs_ui_manager.setup_tabs()

    def _build_indicators(self):
        for widget in self.indicators_frame.winfo_children():
            widget.destroy()

        if self.app_state.df_filtrado is None or self.app_state.df_filtrado.empty:
            customtkinter.CTkLabel(self.indicators_frame, text="Nenhum dado disponível para os filtros selecionados.", font=self.font_normal).pack()
            return

        df = self.app_state.df_filtrado
        total_vendas = df[COL_VALOR].sum() if COL_VALOR in df.columns else 0
        media_vendas = 0
        if COL_VALOR in df.columns and df[COL_VALOR].notna().any():
            media_vendas = df[COL_VALOR].mean()
        num_transacoes = df.shape[0]

        metrics_data = [
            ("Total de Vendas", f"$ {total_vendas:,.2f}"),
            ("Ticket Médio", f"$ {media_vendas:,.2f}"),
            ("Número de Transações", f"{num_transacoes}")
        ]

        for i, (label, value) in enumerate(metrics_data):
            metric_frame = customtkinter.CTkFrame(self.indicators_frame, border_width=1)
            metric_frame.pack(side="left", fill="x", expand=True, padx=5)
            customtkinter.CTkLabel(metric_frame, text=label, font=self.font_metric_label).pack(pady=(5,0))
            customtkinter.CTkLabel(metric_frame, text=value, font=self.font_metric_value).pack(pady=(0,5))

    def _update_dashboard_content(self):
        self._build_indicators()
        if self.tabs_ui_manager:
            self.tabs_ui_manager.update_all_tabs()

    def _clear_tab_frame(self, tab_frame):
        for widget in tab_frame.winfo_children():
            widget.destroy()

    def embed_matplotlib_figure(self, fig, parent_frame):
        self._clear_tab_frame(parent_frame)
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(side="top", fill="both", expand=True)
        return canvas

    def _show_no_data_message(self, parent_frame, custom_message=None):
        self._clear_tab_frame(parent_frame)
        message_text = custom_message or "Nenhum dado disponível para os filtros selecionados."
        customtkinter.CTkLabel(parent_frame, text=message_text, font=self.font_header).pack(pady=20)

if __name__ == "__main__":
    if not os.path.exists(DATABASE_NAME):
        try:
            inicializar_banco_de_dados()
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível inicializar o banco de dados: {e}\nVerifique o arquivo {resource_path_backend} para mais detalhes.")
            sys.exit(1)

    app = DashboardApp()
    app.mainloop()