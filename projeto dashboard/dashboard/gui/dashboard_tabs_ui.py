import tkinter as tk
import customtkinter
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np
from tksheet import Sheet

from backend import (
    COL_CATEGORIA, COL_NOME_PRODUTO, COL_VALOR,
    COL_AVALIACAO, COL_CONTAGEM_AVALIACOES, COL_PERCENTUAL_DESCONTO,
    COL_SENTIMENTO, COL_PRECO
)

class DashboardTabsUIManager:
    def __init__(self, app, notebook):
        self.app = app
        self.notebook = notebook
        self.tab_frames = {}

        self.font_normal = self.app.font_normal
        self.font_bold = self.app.font_bold
        self.font_header = self.app.font_header
        self.font_title = self.app.font_title

        self.top_n_var = tk.IntVar(value=10)
        self._top_n_var_trace_set_up = False
        self.current_top_n_label_widget = None

        self.geral_chart_frame = None
        self.geral_product_list_frame = None
        self.top_produtos_chart_frame = None
        self.produtos_por_categoria_chart_frame = None

        self.tabs_config = [
            ("Visão Geral", self.build_tab_geral),
            ("Análise de Produtos", self.build_tab_produtos),
            ("Preços & Avaliações", self.build_tab_precos_avaliacoes),
            ("Exploração Avançada", self.build_tab_matplotlib_avancado),
            ("Visualizações 3D", self.build_tab_3d),
            ("Análise de Feedbacks", self.build_tab_sentimento),
            ("Dados Detalhados", self.build_tab_dados_detalhados)
        ]

    def setup_tabs(self):
        for titulo, _ in self.tabs_config:
            tab = self.notebook.add(titulo)
            self.tab_frames[titulo] = tab

    def update_all_tabs(self):
        if hasattr(self.app, 'app_state') and self.app.app_state.df_filtrado is not None:
            for titulo, builder_func in self.tabs_config:
                if titulo in self.tab_frames:
                    builder_func(self.tab_frames[titulo])

    # --- Métodos de Construção das Abas ---

    def build_tab_geral(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Performance Geral de Vendas", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado

        self.geral_chart_frame = customtkinter.CTkFrame(tab_frame)
        self.geral_chart_frame.pack(fill="both", expand=True, pady=5)

        geral_buttons_frame = customtkinter.CTkFrame(tab_frame, fg_color="transparent")
        geral_buttons_frame.pack(fill="x", pady=(10, 5))
        customtkinter.CTkLabel(geral_buttons_frame, text="Interagir com Produtos:", font=self.font_bold).pack(side="left", padx=5)
        customtkinter.CTkButton(
            geral_buttons_frame, text="Mostrar Top 10 Produtos (Geral)",
            command=self._show_top_general_products, font=self.font_normal
        ).pack(side="left", padx=5)
        customtkinter.CTkButton(
            geral_buttons_frame, text="Mostrar Produtos da Categoria Atual",
            command=self._show_products_in_current_category, font=self.font_normal
        ).pack(side="left", padx=5)

        customtkinter.CTkLabel(tab_frame, text="Lista de Produtos:", font=self.font_bold).pack(anchor="w", pady=(10, 5))
        self.geral_product_list_frame = customtkinter.CTkScrollableFrame(tab_frame, height=200)
        self.geral_product_list_frame.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(self.geral_product_list_frame, text="Clique nos botões acima para ver a lista de produtos.", font=self.font_normal).pack(pady=10)

        if df is None or df.empty:
            self.app._show_no_data_message(self.geral_chart_frame)
            return

        if COL_CATEGORIA in df.columns and COL_VALOR in df.columns:
            vendas_por_categoria = df.groupby(COL_CATEGORIA)[COL_VALOR].sum().reset_index()
            vendas_por_categoria = vendas_por_categoria[vendas_por_categoria[COL_VALOR] > 0]
            vendas_por_categoria = vendas_por_categoria.sort_values(by=COL_VALOR, ascending=False)

            if not vendas_por_categoria.empty:
                top_n = 5
                vendas_para_plotar = vendas_por_categoria.head(top_n)
                if len(vendas_por_categoria) > top_n:
                    outras_categorias_soma = vendas_por_categoria.iloc[top_n:][COL_VALOR].sum()
                    if outras_categorias_soma > 0:
                        outros_df = pd.DataFrame([{COL_CATEGORIA: "Outros", COL_VALOR: outras_categorias_soma}])
                        vendas_para_plotar = pd.concat([vendas_para_plotar, outros_df], ignore_index=True)
                
                fig = Figure(figsize=(8, 5), dpi=100)
                ax = fig.add_subplot(111)
                sns.barplot(x=COL_CATEGORIA, y=COL_VALOR, data=vendas_para_plotar, ax=ax, palette="viridis", hue=COL_CATEGORIA, legend=False)
                ax.set_title(f"Top Categorias por Vendas")
                ax.set_xlabel(COL_CATEGORIA)
                ax.set_ylabel(f"{COL_VALOR} ($)")
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                fig.tight_layout()
                self.app.embed_matplotlib_figure(fig, self.geral_chart_frame)
            else:
                self.app._show_no_data_message(self.geral_chart_frame, f"Nenhuma venda positiva para {COL_CATEGORIA} nos filtros.")
        else:
            self.app._show_no_data_message(self.geral_chart_frame, f"Gráfico de Vendas por {COL_CATEGORIA} desabilitado (colunas ausentes).")

    def _show_top_general_products(self):
        if not self.geral_product_list_frame or not self.geral_product_list_frame.winfo_exists(): return
        self.app._clear_tab_frame(self.geral_product_list_frame)
        df = self.app.app_state.df_filtrado

        if df is None or df.empty or COL_NOME_PRODUTO not in df.columns or COL_VALOR not in df.columns:
            customtkinter.CTkLabel(self.geral_product_list_frame, text="Dados insuficientes para mostrar produtos.", font=self.font_normal).pack(pady=10)
            return

        top_produtos = df.groupby(COL_NOME_PRODUTO)[COL_VALOR].sum().nlargest(10).reset_index()
        if top_produtos.empty:
             customtkinter.CTkLabel(self.geral_product_list_frame, text="Nenhum produto encontrado.", font=self.font_normal).pack(pady=10)
             return
        customtkinter.CTkLabel(self.geral_product_list_frame, text="Top 10 Produtos (Geral):", font=self.font_bold).pack(anchor="w")
        for index, row in top_produtos.iterrows():
            product_info = f"{index + 1}. {row[COL_NOME_PRODUTO]} - Vendas: ${row[COL_VALOR]:,.2f}"
            customtkinter.CTkLabel(self.geral_product_list_frame, text=product_info, font=self.font_normal, anchor="w").pack(fill="x", padx=5)

    def _show_products_in_current_category(self):
        if not self.geral_product_list_frame or not self.geral_product_list_frame.winfo_exists(): return
        self.app._clear_tab_frame(self.geral_product_list_frame)
        df = self.app.app_state.df_filtrado
        categoria_selecionada = self.app.categoria_var.get()

        if df is None or df.empty or COL_NOME_PRODUTO not in df.columns or COL_CATEGORIA not in df.columns:
            customtkinter.CTkLabel(self.geral_product_list_frame, text="Dados insuficientes.", font=self.font_normal).pack(pady=10)
            return
        if categoria_selecionada == "Todas":
             customtkinter.CTkLabel(self.geral_product_list_frame, text="Selecione uma categoria no filtro.", font=self.font_normal).pack(pady=10)
             return
        produtos_categoria = df[df[COL_CATEGORIA] == categoria_selecionada].copy()
        if produtos_categoria.empty:
             customtkinter.CTkLabel(self.geral_product_list_frame, text=f"Nenhum produto em '{categoria_selecionada}'.", font=self.font_normal).pack(pady=10)
             return
        produtos_categoria = produtos_categoria.sort_values(by=COL_VALOR, ascending=False)
        customtkinter.CTkLabel(self.geral_product_list_frame, text=f"Produtos em '{categoria_selecionada}':", font=self.font_bold).pack(anchor="w")
        for index, row in produtos_categoria.iterrows():
             product_info = f"- {row[COL_NOME_PRODUTO]} - Vendas: ₹{row[COL_VALOR]:,.2f}"
             customtkinter.CTkLabel(self.geral_product_list_frame, text=product_info, font=self.font_normal, anchor="w").pack(fill="x", padx=5)

    def build_tab_produtos(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Análise Detalhada de Produtos", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado

        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame)
            return

        # Criar um frame rolável para conter todos os elementos da aba
        scrollable_content_frame = customtkinter.CTkScrollableFrame(tab_frame)
        scrollable_content_frame.pack(fill="both", expand=True)

        controls_frame = customtkinter.CTkFrame(scrollable_content_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=5)
        customtkinter.CTkLabel(controls_frame, text="Top N Produtos:", font=self.font_normal).pack(side="left", padx=5)
        
        top_n_slider = customtkinter.CTkSlider(
            controls_frame, from_=3, to=20, variable=self.top_n_var,
            orientation="horizontal", command=lambda val: self._update_tab_produtos_charts()
        )
        top_n_slider.pack(side="left", padx=5, fill="x", expand=True)
        
        self.current_top_n_label_widget = customtkinter.CTkLabel(controls_frame, text=f"{self.top_n_var.get()}", font=self.font_normal)
        self.current_top_n_label_widget.pack(side="left", padx=5)
        
        if not self._top_n_var_trace_set_up:
            def _update_slider_label_callback(*args):
                if self.current_top_n_label_widget and self.current_top_n_label_widget.winfo_exists():
                    self.current_top_n_label_widget.configure(text=f"{self.top_n_var.get()}")
            self.top_n_var.trace_add("write", _update_slider_label_callback)
            self._top_n_var_trace_set_up = True

        self.top_produtos_chart_frame = customtkinter.CTkFrame(scrollable_content_frame)
        self.top_produtos_chart_frame.pack(fill="both", expand=True, pady=5)
        self.produtos_por_categoria_chart_frame = customtkinter.CTkFrame(scrollable_content_frame)
        self.produtos_por_categoria_chart_frame.pack(fill="both", expand=True, pady=5)
        self._update_tab_produtos_charts()

    def _update_tab_produtos_charts(self):
        df = self.app.app_state.df_filtrado
        if df is None or df.empty:
            if self.top_produtos_chart_frame and self.top_produtos_chart_frame.winfo_exists():
                 self.app._show_no_data_message(self.top_produtos_chart_frame)
            if self.produtos_por_categoria_chart_frame and self.produtos_por_categoria_chart_frame.winfo_exists():
                 self.app._show_no_data_message(self.produtos_por_categoria_chart_frame)
            return

        if self.top_produtos_chart_frame and self.top_produtos_chart_frame.winfo_exists():
            if COL_NOME_PRODUTO in df.columns and COL_VALOR in df.columns:
                top_n = self.top_n_var.get()
                top_produtos = df.groupby(COL_NOME_PRODUTO)[COL_VALOR].sum().nlargest(top_n).reset_index()
                if not top_produtos.empty:
                    max_len_pn = 25
                    top_produtos = top_produtos.copy()
                    top_produtos[COL_NOME_PRODUTO + '_display'] = top_produtos[COL_NOME_PRODUTO].apply(
                        lambda x: x[:max_len_pn] if len(x) > max_len_pn else x
                    )

                    fig = Figure(figsize=(8, 5), dpi=100)
                    ax = fig.add_subplot(111)
                    sns.barplot(x=COL_NOME_PRODUTO + '_display', y=COL_VALOR, data=top_produtos, ax=ax, hue=COL_NOME_PRODUTO + '_display', palette="viridis", legend=False)
                    ax.set_title(f"Top {top_n} Produtos por {COL_VALOR}")
                    ax.set_xlabel("Produto")
                    ax.set_ylabel(f"{COL_VALOR} ($)")
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
                    fig.tight_layout()
                    self.app.embed_matplotlib_figure(fig, self.top_produtos_chart_frame)
                else:
                    self.app._show_no_data_message(self.top_produtos_chart_frame, "Nenhum produto para ranking.")
            else:
                self.app._show_no_data_message(self.top_produtos_chart_frame, f"Colunas para ranking ausentes.")

        if self.produtos_por_categoria_chart_frame and self.produtos_por_categoria_chart_frame.winfo_exists():
            if COL_CATEGORIA in df.columns:
                contagem_categoria = df[COL_CATEGORIA].value_counts().reset_index()
                if not contagem_categoria.empty:
                    contagem_categoria.columns = [COL_CATEGORIA, 'Contagem']
                    fig2 = Figure(figsize=(8, 5), dpi=100)
                    ax2 = fig2.add_subplot(111)
                    sns.barplot(x=COL_CATEGORIA, y='Contagem', data=contagem_categoria, ax=ax2, hue=COL_CATEGORIA, palette="Set3", legend=False)
                    ax2.set_title(f"Produtos por {COL_CATEGORIA}")
                    ax2.set_xlabel(COL_CATEGORIA)
                    ax2.set_ylabel("Nº Produtos")
                    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right', fontsize=8)
                    fig2.tight_layout()
                    self.app.embed_matplotlib_figure(fig2, self.produtos_por_categoria_chart_frame)
                else:
                    self.app._show_no_data_message(self.produtos_por_categoria_chart_frame, "Nenhuma categoria encontrada.")
            else:
                self.app._show_no_data_message(self.produtos_por_categoria_chart_frame, f"Coluna {COL_CATEGORIA} ausente.")

    def build_tab_precos_avaliacoes(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text=f"Análise de Preços ({COL_VALOR}), Descontos e Avaliações", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado
        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame)
            return

        scrollable_charts_frame = customtkinter.CTkScrollableFrame(tab_frame)
        scrollable_charts_frame.pack(fill="both", expand=True)

        chart1_frame = customtkinter.CTkFrame(scrollable_charts_frame, height=400)
        chart1_frame.pack(fill="x", expand=True, pady=5)
        if COL_VALOR in df.columns and df[COL_VALOR].notna().any():
            fig1 = Figure(figsize=(7, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            sns.histplot(df[COL_VALOR], kde=True, ax=ax1, color="skyblue", bins=30)
            ax1.set_title(f"Distribuição de Preços ({COL_VALOR} com Desconto)")
            ax1.set_xlabel("Preço (₹)")
            ax1.set_ylabel("Frequência")
            fig1.tight_layout()
            self.app.embed_matplotlib_figure(fig1, chart1_frame)
        else:
            self.app._show_no_data_message(chart1_frame, f"Dados de {COL_VALOR} insuficientes.")

        chart2_frame = customtkinter.CTkFrame(scrollable_charts_frame, height=450)
        chart2_frame.pack(fill="x", expand=True, pady=5)
        if COL_VALOR in df.columns and COL_AVALIACAO in df.columns and df[COL_AVALIACAO].notna().any():
            df_scatter = df.dropna(subset=[COL_AVALIACAO, COL_VALOR])
            if not df_scatter.empty:
                fig2 = Figure(figsize=(7, 4.3), dpi=100)
                ax2 = fig2.add_subplot(111)
                scatter = ax2.scatter(df_scatter[COL_AVALIACAO], df_scatter[COL_VALOR], c=df_scatter[COL_AVALIACAO], cmap="plasma", alpha=0.7)
                ax2.set_title(f"Preço ({COL_VALOR}) vs. {COL_AVALIACAO}")
                ax2.set_xlabel(COL_AVALIACAO)
                ax2.set_ylabel("Preço ($)")
                cbar = fig2.colorbar(scatter, ax=ax2)
                cbar.set_label(COL_AVALIACAO)
                fig2.tight_layout()
                self.app.embed_matplotlib_figure(fig2, chart2_frame)
            else:
                self.app._show_no_data_message(chart2_frame, f"Dados de {COL_VALOR} ou {COL_AVALIACAO} insuficientes.")
        else:
            self.app._show_no_data_message(chart2_frame, f"Colunas {COL_VALOR} ou {COL_AVALIACAO} ausentes.")

        chart3_frame = customtkinter.CTkFrame(scrollable_charts_frame, height=520)
        chart3_frame.pack(fill="x", expand=True, pady=5)
        if COL_NOME_PRODUTO in df.columns and COL_PERCENTUAL_DESCONTO in df.columns and df[COL_PERCENTUAL_DESCONTO].notna().any():
            top_n_desconto = 10
            produtos_maior_desconto = df.nlargest(top_n_desconto, COL_PERCENTUAL_DESCONTO)
            if not produtos_maior_desconto.empty:
                max_len_pn = 25
                produtos_maior_desconto = produtos_maior_desconto.copy()
                produtos_maior_desconto[COL_NOME_PRODUTO + '_display'] = produtos_maior_desconto[COL_NOME_PRODUTO].apply(
                    lambda x: x[:max_len_pn] if len(x) > max_len_pn else x
                )
                fig3 = Figure(figsize=(7, 5.0), dpi=100)
                ax3 = fig3.add_subplot(111)
                sns.barplot(x=COL_NOME_PRODUTO + '_display', y=COL_PERCENTUAL_DESCONTO, data=produtos_maior_desconto, ax=ax3, palette="OrRd")
                ax3.set_title(f"Top {top_n_desconto} Produtos por {COL_PERCENTUAL_DESCONTO}")
                ax3.set_xlabel("Produto")
                ax3.set_ylabel("Desconto (%)")
                ax3.tick_params(axis='x', rotation=65, labelsize=8)
                fig3.subplots_adjust(bottom=0.3)
                fig3.tight_layout()
                self.app.embed_matplotlib_figure(fig3, chart3_frame)
            else:
                self.app._show_no_data_message(chart3_frame, "Nenhum produto com desconto.")
        else:
            self.app._show_no_data_message(chart3_frame, f"Colunas {COL_NOME_PRODUTO} ou {COL_PERCENTUAL_DESCONTO} ausentes.")

    def build_tab_matplotlib_avancado(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Exploração Avançada com Matplotlib & Seaborn", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado
        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame)
            return

        scrollable_charts_frame = customtkinter.CTkScrollableFrame(tab_frame)
        scrollable_charts_frame.pack(fill="both", expand=True)

        chart_configs = [
            (f"Box Plot: {COL_VALOR} por {COL_CATEGORIA}", [COL_CATEGORIA, COL_VALOR],
             lambda ax, data: sns.boxplot(x=COL_CATEGORIA, y=COL_VALOR, data=data, ax=ax, palette="Set3"),
             {'xlabel': COL_CATEGORIA, 'ylabel': f'{COL_VALOR} ($)', 'rotation': 45}),
            (f"Violin Plot: {COL_AVALIACAO} por {COL_CATEGORIA}", [COL_CATEGORIA, COL_AVALIACAO],
             lambda ax, data: sns.violinplot(x=COL_CATEGORIA, y=COL_AVALIACAO, data=data.dropna(subset=[COL_AVALIACAO]), ax=ax, palette="Pastel1"),
             {'xlabel': COL_CATEGORIA, 'ylabel': COL_AVALIACAO, 'rotation': 45},
             lambda d: d[COL_AVALIACAO].notna().any()),
            (f"Scatter Plot: {COL_VALOR} vs. {COL_PERCENTUAL_DESCONTO}", [COL_VALOR, COL_PERCENTUAL_DESCONTO, COL_CATEGORIA],
             lambda ax, data: sns.scatterplot(x=COL_PERCENTUAL_DESCONTO, y=COL_VALOR, data=data.dropna(subset=[COL_PERCENTUAL_DESCONTO, COL_VALOR]), ax=ax, hue=COL_CATEGORIA, palette="viridis", alpha=0.7),
             {'xlabel': f'{COL_PERCENTUAL_DESCONTO} (%)', 'ylabel': f'{COL_VALOR} (₹)'},
             lambda d: d[COL_PERCENTUAL_DESCONTO].notna().any()),
            ("Heatmap de Correlação", [],
             lambda ax, data: sns.heatmap(data.corr(numeric_only=True), annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, ax=ax),
             {},
             lambda d: len(d.select_dtypes(include=np.number).columns) > 1,
             lambda d: d.select_dtypes(include=np.number)),
            (f"Count Plot: Produtos por {COL_CATEGORIA}", [COL_CATEGORIA],
             lambda ax, data: sns.countplot(y=COL_CATEGORIA, data=data, ax=ax, palette="Spectral", order = data[COL_CATEGORIA].value_counts().index),
             {'xlabel': 'Contagem', 'ylabel': COL_CATEGORIA}),
            (f"Joint Plot: {COL_AVALIACAO} vs. {COL_CONTAGEM_AVALIACOES}", [COL_AVALIACAO, COL_CONTAGEM_AVALIACOES],
             None, {}, lambda d: d[COL_AVALIACAO].notna().any() and d[COL_CONTAGEM_AVALIACOES].notna().any())
        ]

        for title, req_cols, plot_func, labels, *prereq_and_prep in chart_configs:
            chart_f = customtkinter.CTkFrame(scrollable_charts_frame, height=450)
            chart_f.pack(fill="x", expand=True, pady=10)
            customtkinter.CTkLabel(chart_f, text=title, font=self.font_bold).pack(anchor="w")
            
            prereq_check = prereq_and_prep[0] if prereq_and_prep else lambda d: True
            data_prep_func = prereq_and_prep[1] if len(prereq_and_prep) > 1 else lambda d: d

            if all(col in df.columns for col in req_cols) and prereq_check(df):
                plot_data = data_prep_func(df)
                if plot_data is None or plot_data.empty:
                    self.app._show_no_data_message(chart_f, f"Dados insuficientes para '{title}'.")
                    continue
                if title.startswith("Joint Plot"):
                    try:
                        joint_fig = sns.jointplot(x=COL_AVALIACAO, y=COL_CONTAGEM_AVALIACOES, data=df.dropna(subset=[COL_AVALIACAO, COL_CONTAGEM_AVALIACOES]), kind='scatter', color='skyblue', marginal_kws=dict(bins=15, fill=True))
                        joint_fig.fig.suptitle(f'{COL_AVALIACAO} vs. {COL_CONTAGEM_AVALIACOES} (Marginais)', y=1.02, fontsize=10)
                        self.app.embed_matplotlib_figure(joint_fig.fig, chart_f)
                    except Exception as e:
                        self.app._show_no_data_message(chart_f, f"Erro Joint Plot: {e}")
                elif plot_func:
                    fig = Figure(figsize=(7, 4.2), dpi=100)
                    ax = fig.add_subplot(111)
                    plot_func(ax, plot_data)
                    ax.set_title(title, fontsize=10)
                    if 'xlabel' in labels: ax.set_xlabel(labels['xlabel'])
                    if 'rotation' in labels: plt.setp(ax.get_xticklabels(), rotation=labels['rotation'], ha='right' if labels['rotation'] > 0 else 'center')
                    if 'ylabel' in labels: ax.set_ylabel(labels['ylabel'])
                    fig.tight_layout()
                    self.app.embed_matplotlib_figure(fig, chart_f)
            else:
                self.app._show_no_data_message(chart_f, f"Colunas ({', '.join(req_cols)}) ou pré-requisitos não atendidos.")

    def build_tab_3d(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Visualizações 3D Interativas", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado
        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame)
            return

        cols_3d_mpl = [COL_VALOR, COL_AVALIACAO, COL_CONTAGEM_AVALIACOES, COL_CATEGORIA]
        if all(col in df.columns for col in cols_3d_mpl) and all(df[col].notna().any() for col in [COL_VALOR, COL_AVALIACAO, COL_CONTAGEM_AVALIACOES]):
            df_3d = df.dropna(subset=cols_3d_mpl)
            if not df_3d.empty:
                try:
                    fig = Figure(figsize=(8, 6), dpi=100)
                    ax = fig.add_subplot(111, projection='3d')
                    unique_categories = df_3d[COL_CATEGORIA].unique()
                    colors = plt.get_cmap('viridis', len(unique_categories))
                    category_color_map = {cat: colors(i) for i, cat in enumerate(unique_categories)}
                    for category in unique_categories:
                        subset = df_3d[df_3d[COL_CATEGORIA] == category]
                        ax.scatter(subset[COL_AVALIACAO], subset[COL_CONTAGEM_AVALIACOES], subset[COL_VALOR], label=category, color=category_color_map[category])
                    ax.set_xlabel(COL_AVALIACAO)
                    ax.set_ylabel(COL_CONTAGEM_AVALIACOES)
                    ax.set_zlabel(COL_VALOR + " (₹)")
                    ax.set_title(f"3D: {COL_AVALIACAO}, {COL_CONTAGEM_AVALIACOES}, {COL_VALOR}", fontsize=10)
                    ax.legend(title=COL_CATEGORIA, fontsize=8)
                    fig.tight_layout()
                    self.app.embed_matplotlib_figure(fig, tab_frame)
                    customtkinter.CTkLabel(tab_frame, text="Nota: Interatividade 3D limitada. Para rotação, use a barra de ferramentas Matplotlib ou salve.", wraplength=tab_frame.winfo_width()-20, font=self.font_normal).pack(pady=5)
                except Exception as e:
                     self.app._show_no_data_message(tab_frame, f"Erro ao gerar gráfico 3D: {e}")
            else:
                self.app._show_no_data_message(tab_frame, "Dados insuficientes para 3D após NAs.")
        else:
            self.app._show_no_data_message(tab_frame, f"Colunas para 3D não disponíveis.")

    def build_tab_sentimento(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Análise de Sentimento Baseada em Avaliações", font=self.font_header).pack(anchor="w", pady=(0,10))
        df = self.app.app_state.df_filtrado
        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame)
            return
        if COL_SENTIMENTO not in df.columns:
            self.app._show_no_data_message(tab_frame, f"Coluna '{COL_SENTIMENTO}' não gerada.")
            return

        chart1_frame = customtkinter.CTkFrame(tab_frame, height=350)
        chart1_frame.pack(fill="x", expand=True, pady=5)
        sent_counts = df[COL_SENTIMENTO].value_counts().reset_index()
        sent_counts.columns = [COL_SENTIMENTO, 'Contagem']
        color_map = {'Positivo': '#2ca02c', 'Neutro': '#1f77b4', 'Negativo': '#d62728', 'Não Avaliado': '#7f7f7f'}
        category_orders = ["Positivo", "Neutro", "Negativo", "Não Avaliado"]
        sent_counts_ordered = pd.DataFrame({COL_SENTIMENTO: category_orders}).merge(sent_counts, on=COL_SENTIMENTO, how='left').fillna(0)

        if not sent_counts_ordered.empty:
            fig1 = Figure(figsize=(7, 3.5), dpi=100)
            ax1 = fig1.add_subplot(111)
            sns.barplot(x=COL_SENTIMENTO, y='Contagem', data=sent_counts_ordered, ax=ax1, palette=[color_map.get(s, "#cccccc") for s in sent_counts_ordered[COL_SENTIMENTO]], order=category_orders)
            ax1.set_title("Distribuição de Sentimento")
            ax1.set_xlabel("Sentimento")
            ax1.set_ylabel("Nº Produtos")
            fig1.tight_layout()
            self.app.embed_matplotlib_figure(fig1, chart1_frame)
        else:
            self.app._show_no_data_message(chart1_frame, "Sem dados de sentimento.")

        chart2_frame = customtkinter.CTkFrame(tab_frame, height=450)
        chart2_frame.pack(fill="x", expand=True, pady=5)
        if COL_CATEGORIA in df.columns:
            sent_cat = df.groupby([COL_CATEGORIA, COL_SENTIMENTO]).size().reset_index(name='Contagem')
            if not sent_cat.empty:
                fig2 = Figure(figsize=(8, 4.5), dpi=100)
                ax2 = fig2.add_subplot(111)
                pivot_sent_cat = sent_cat.pivot(index=COL_CATEGORIA, columns=COL_SENTIMENTO, values='Contagem').fillna(0)
                pivot_sent_cat = pivot_sent_cat.reindex(columns=category_orders, fill_value=0)
                pivot_sent_cat.plot(kind='bar', ax=ax2, color=[color_map.get(s, "#cccccc") for s in pivot_sent_cat.columns])
                ax2.set_title(f"{COL_SENTIMENTO} por {COL_CATEGORIA}")
                ax2.set_xlabel(COL_CATEGORIA)
                ax2.set_ylabel("Contagem")
                plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
                ax2.legend(title=COL_SENTIMENTO)
                fig2.tight_layout()
                self.app.embed_matplotlib_figure(fig2, chart2_frame)
            else:
                self.app._show_no_data_message(chart2_frame, "Sem dados de sentimento por categoria.")
        else:
            self.app._show_no_data_message(chart2_frame, f"Coluna {COL_CATEGORIA} ausente.")

    def build_tab_dados_detalhados(self, tab_frame):
        self.app._clear_tab_frame(tab_frame)
        customtkinter.CTkLabel(tab_frame, text="Dados Detalhados Filtrados 📄", font=self.font_header).pack(anchor="w", pady=(0, 10))
        df = self.app.app_state.df_filtrado
        user_can_see = self.app.app_state.user_permissions.get("can_see_details", False)
        if self.app.app_state.user_role == "gerente": user_can_see = True

        if not user_can_see:
            self.app._show_no_data_message(tab_frame, "Você não tem permissão para visualizar dados detalhados.")
            return
        if df is None or df.empty:
            self.app._show_no_data_message(tab_frame, "Nenhum dado disponível para os filtros.")
            return

        cols_mostrar = [COL_NOME_PRODUTO, COL_CATEGORIA, COL_VALOR, COL_AVALIACAO, COL_SENTIMENTO, COL_CONTAGEM_AVALIACOES, COL_PERCENTUAL_DESCONTO, COL_PRECO]
        cols_existentes = [col for col in cols_mostrar if col in df.columns]
        if not cols_existentes:
            self.app._show_no_data_message(tab_frame, "Nenhuma coluna selecionada para exibição está nos dados.")
            return

        df_to_display = df[cols_existentes].copy()
        data_list = df_to_display.values.tolist() if not df_to_display.empty else []

        try:
            sheet = Sheet(tab_frame, data=data_list, headers=cols_existentes)
            sheet.pack(fill="both", expand=True, padx=5, pady=5)
            sheet.enable_bindings()
        except Exception as e:
            customtkinter.CTkLabel(tab_frame, text=f"Erro ao carregar tabela: {e}", text_color="red", font=self.font_normal).pack()
