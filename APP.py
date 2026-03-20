import pandas as pd
import io
from io import BytesIO
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import bcrypt

# 1. Configurações de conexão
url = "https://oudfbraxmwuskdnnlisf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91ZGZicmF4bXd1c2tkbm5saXNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4Nzc5NzQsImV4cCI6MjA4OTQ1Mzk3NH0.QnL67maBxqsfgm4xHmLBYcqPbQ99swjHw3OzndSM9qA"
supabase = create_client(url, key)

# --- 2. FUNÇÕES DE SEGURANÇA (Adicionei a verificar_hash que faltava) ---

def gerar_senha_inicial(senha_numerica):
    hash_gerado = bcrypt.hashpw(str(senha_numerica).encode('utf-8'), bcrypt.gensalt())
    return hash_gerado.decode('utf-8')

def verificar_hash(senha, hash_db):
    # Esta função é essencial para a tela_login funcionar!
    return bcrypt.checkpw(senha.encode('utf-8'), hash_db.encode('utf-8'))

# --- 3. TELA DE LOGIN ---

def tela_login():
    if matricula == "admin" and senha == "1234":
    st.session_state.usuario_logado = "admin"
    st.session_state.nome_admin = "Administrador Master"
    st.rerun()
    
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None
        st.session_state.nome_admin = ""

    if st.session_state.usuario_logado is None:
        # Centraliza a tela de login
        _, col2, _ = st.columns([1,2,1]) 
        with col2:
            st.markdown("### 🏥 Controle de Materiais - Login")
            with st.container(border=True):
                matricula = st.text_input("Matrícula (Usuário)")
                senha = st.text_input("Senha Numérica", type="password", help="Digite apenas números")
                
                if st.button("Acessar Sistema", use_container_width=True):
                    if not matricula or not senha:
                        st.warning("Preencha todos os campos.")
                    elif not senha.isdigit():
                        st.error("A senha deve conter apenas números!")
                    else:
                        res = supabase.table("usuarios").select("*").eq("usuario", matricula).execute()
                        
                        if res.data:
                            user_data = res.data[0]
                            # Agora a função verificar_hash existe e vai funcionar
                            if verificar_hash(senha, user_data["senha_hash"]):
                                st.session_state.usuario_logado = user_data["usuario"]
                                st.session_state.nome_admin = user_data["nome_exibicao"]
                                st.success(f"Conectado como: {user_data['nome_exibicao']}")
                                st.rerun()
                            else:
                                st.error("Senha incorreta.")
                        else:
                            st.error("Matrícula não cadastrada.")
        st.stop() # Bloqueia o app até logar

# --- 4. EXECUÇÃO ---

# IMPORTANTE: Chame a função de login ANTES de criar as abas
tela_login()

# O restante das suas funções (limpar_input, exportar_excel, etc) vem aqui...


def limpar_input_unidade():
    st.session_state["input_create_unidade"] = ""

def exportar_excel(df):
    output = io.BytesIO()
    # Certifique-se de que o engine é o que adicionamos no requirements
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
        
        # Aqui você pode adicionar as formatações de coluna que quiser
        workbook = writer.book
        worksheet = writer.sheets['Inventario']
        
        # Exemplo: Ajustar largura das colunas
        worksheet.set_column('A:Z', 20)
        
    # CRITICAL: O seek(0) é o que garante que o Streamlit leia o arquivo do início
    output.seek(0)
    return output
    
def formato_brasilia(data_iso):
    if not data_iso:
        return ""
    # O Supabase envia algo como "2026-03-19T17:00:00+00:00"
    # Removemos o fuso e convertemos para objeto datetime
    dt_utc = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
    # Subtrai 3 horas para Brasília
    dt_br = dt_utc - timedelta(hours=3)
    return dt_br.strftime('%d/%m/%Y %H:%M')

# Função para definir o emoji de status
def cor(s):
    if s == "trocar_urgente":
        return "🔴"
    elif s == "trocar_nao_urgente":
        return "🟡"
    else:
        return "🟢"


@st.cache_data
def get_unidades():
    return supabase.table("unidades").select("*").execute().data

@st.cache_data
def get_ambientes():
    return supabase.table("ambientes").select("*").execute().data

@st.cache_data
def get_materiais():
    return supabase.table("materiais").select("*").execute().data

@st.cache_data
def get_itens():
    return supabase.table("itens_inventario").select("*").execute().data







aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Unidades", 
    "Ambientes", 
    "Editar Materiais", 
    "Controle de Materiais",
    "Relatórios"
])


with aba1:
    st.header("🏥 Unidades")

    # 1. CARREGAMENTO DOS DADOS VIA CACHE
    unidades_data = get_unidades()

    # -------------------------
    # CRIAR UNIDADE
    # -------------------------
    if "reset_count" not in st.session_state:
        st.session_state.reset_count = 0
    
    # 2. Crie uma chave única baseada nesse contador
    chave_dinamica = f"input_unidade_{st.session_state.reset_count}"
    
    # 3. Use essa chave no text_input
    nome_unidade = st.text_input("Nome da unidade", key=chave_dinamica)
    
    if st.button("Criar Unidade", key="btn_create_unidade"):
        if not nome_unidade:
            st.warning("Digite o nome da unidade")
        else:
            existe = [u for u in unidades_data if u["nome"].lower() == nome_unidade.lower()]
            
            if existe:
                st.warning(f"A unidade '{nome_unidade}' já existe.")
            else:
                try:
                    # Faz o insert normalmente
                    supabase.table("unidades").insert({"nome": nome_unidade}).execute()
                    
                    st.success(f"✅ Unidade '{nome_unidade}' criada!")
                    
                    # --- AQUI ESTÁ O TRUQUE ---
                    # Aumentamos o contador. No próximo rerun, a chave do input muda 
                    # e o Streamlit renderiza um campo NOVO e VAZIO.
                    st.session_state.reset_count += 1
                    
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error("Erro ao salvar:")
                    st.exception(e)

    # -------------------------
    # BUSCA (Agora filtrando os dados cacheados)
    # -------------------------
    busca = st.text_input("🔎 Buscar unidade", key="input_busca_unidade")

    unidades_exibicao = unidades_data

    if busca:
        unidades_exibicao = [u for u in unidades_data if busca.lower() in u["nome"].lower()]

    # -------------------------
    # LISTAGEM COM AÇÕES
    # -------------------------
    for u in unidades_exibicao:
        col1, col2, col3 = st.columns([6,1,1])

        # Nome
        with col1:
            st.write(u["nome"])

        # Editar
        with col2:
            if st.button("✏️", key=f"edit_{u['id']}"):
                st.session_state["edit_unidade"] = u

        # Deletar
        with col3:
            if st.button("🗑️", key=f"del_{u['id']}"):
                st.session_state["confirm_delete_unidade"] = u

    # -------------------------
    # CONFIRMAÇÃO DE EXCLUSÃO
    # -------------------------
    if "confirm_delete_unidade" in st.session_state:

        unidade = st.session_state["confirm_delete_unidade"]

        st.warning(f"A unidade '{unidade['nome']}' pode ter ambientes vinculados.")
        st.write("Deseja excluir a unidade e TODOS os dados relacionados?")

        col1, col2 = st.columns(2)

        # CONFIRMAR
        with col1:
            if st.button("Sim, excluir tudo", key="btn_confirm_del_final"):

                try:
                    # Buscar ambientes da unidade (aqui usamos query direta para garantir cascata correta)
                    ambientes = supabase.table("ambientes") \
                        .select("*") \
                        .eq("unidade_id", unidade["id"]) \
                        .execute().data

                    for amb in ambientes:
                        # Deletar itens do ambiente
                        supabase.table("itens_inventario") \
                            .delete() \
                            .eq("ambiente_id", amb["id"]) \
                            .execute()

                        # Deletar ambiente
                        supabase.table("ambientes") \
                            .delete() \
                            .eq("id", amb["id"]) \
                            .execute()

                    # Deletar unidade
                    supabase.table("unidades") \
                        .delete() \
                        .eq("id", unidade["id"]) \
                        .execute()

                    st.success("Unidade e todos os dados foram excluídos!")
                    # Limpa o cache global após a exclusão
                    st.cache_data.clear()
                    del st.session_state["confirm_delete_unidade"]
                    st.rerun()

                except Exception as e:
                    st.error("Erro ao excluir:")
                    st.write(e)

        # CANCELAR
        with col2:
            if st.button("Cancelar", key="btn_cancel_del"):
                del st.session_state["confirm_delete_unidade"]
                st.rerun()

    # -------------------------
    # EDITAR UNIDADE
    # -------------------------
    if "edit_unidade" in st.session_state:
        st.subheader("✏️ Editar Unidade")

        unidade = st.session_state["edit_unidade"]

        novo_nome = st.text_input(
            "Novo nome",
            value=unidade["nome"],
            key="input_edit_nome"
        )

        if st.button("Salvar alteração", key="btn_save_edit"):
            supabase.table("unidades") \
                .update({"nome": novo_nome}) \
                .eq("id", unidade["id"]) \
                .execute()

            st.success("Atualizado!")
            # Limpa o cache para atualizar o nome na lista
            st.cache_data.clear()
            del st.session_state["edit_unidade"]
            st.rerun()
            
with aba2:
    st.header("🏢 Ambientes")

    # 1. Inicializa o contador de reset específico para Ambientes
    if "reset_amb_count" not in st.session_state:
        st.session_state.reset_amb_count = 0

    # -------------------------
    # BUSCAR UNIDADE (USANDO CACHE)
    # -------------------------
    busca_unidade = st.text_input("🔎 Buscar unidade", key="busca_unidade_amb")
    unidades_data = get_unidades() 

    unidades_filtradas = unidades_data
    if busca_unidade:
        unidades_filtradas = [u for u in unidades_data if busca_unidade.lower() in u["nome"].lower()]

    if not unidades_filtradas:
        st.warning("Nenhuma unidade encontrada")
    else:
        unidade_sel = st.selectbox(
            "Selecione a unidade",
            unidades_filtradas,
            format_func=lambda x: x["nome"],
            key="sb_unidade_amb"
        )

        # -------------------------
        # CRIAR AMBIENTE
        # -------------------------
        st.subheader("➕ Novo Ambiente")

        # 2. Chave dinâmica para o input de nome do ambiente
        chave_amb = f"input_nome_amb_{st.session_state.reset_amb_count}"
        nome_ambiente = st.text_input("Nome do ambiente", key=chave_amb)

        if st.button("Criar Ambiente"):
            if not nome_ambiente:
                st.warning("Digite o nome do ambiente")
            else:
                try:
                    supabase.table("ambientes").insert({
                        "nome": nome_ambiente.strip(),
                        "unidade_id": unidade_sel["id"]
                    }).execute()

                    st.success(f"✅ Ambiente '{nome_ambiente}' criado na unidade {unidade_sel['nome']}!")
                    
                    # 3. O Pulo do Gato: Incrementa o contador para limpar o campo
                    st.session_state.reset_amb_count += 1
                    
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        # -------------------------
        # LISTAR AMBIENTES DA UNIDADE (USANDO CACHE)
        # -------------------------
        st.subheader("📋 Ambientes da unidade")

        # Usando a função com cache
        todos_ambientes = get_ambientes()
        
        # Filtramos em memória os ambientes que pertencem à unidade selecionada
        ambientes_da_unidade = [a for a in todos_ambientes if a["unidade_id"] == unidade_sel["id"]]

        if not ambientes_da_unidade:
            st.info("Nenhum ambiente cadastrado")
        else:
            for a in ambientes_da_unidade:
                col1, col2, col3 = st.columns([6,1,1])

                with col1:
                    st.write(a["nome"])

                with col2:
                    if st.button("✏️", key=f"edit_amb_{a['id']}"):
                        st.session_state["edit_ambiente"] = a

                with col3:
                    if st.button("🗑️", key=f"del_amb_{a['id']}"):
                        st.session_state["confirm_delete_ambiente"] = a

    # -------------------------
    # CONFIRMAR EXCLUSÃO
    # -------------------------
    if "confirm_delete_ambiente" in st.session_state:
        amb = st.session_state["confirm_delete_ambiente"]
        st.warning(f"O ambiente '{amb['nome']}' será excluído com todos os itens.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Sim, excluir", key="btn_conf_del_amb"):
                try:
                    # deletar itens
                    supabase.table("itens_inventario").delete().eq("ambiente_id", amb["id"]).execute()
                    # deletar ambiente
                    supabase.table("ambientes").delete().eq("id", amb["id"]).execute()

                    st.success("Ambiente excluído!")
                    # Limpa o cache após exclusão
                    st.cache_data.clear()
                    del st.session_state["confirm_delete_ambiente"]
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro: {e}")

        with col2:
            if st.button("Cancelar", key="btn_canc_del_amb"):
                del st.session_state["confirm_delete_ambiente"]
                st.rerun()

    # -------------------------
    # EDITAR AMBIENTE
    # -------------------------
    if "edit_ambiente" in st.session_state:
        amb = st.session_state["edit_ambiente"]
        st.subheader("✏️ Editar Ambiente")
        novo_nome = st.text_input("Novo nome", value=amb["nome"], key="input_edit_amb")

        if st.button("Salvar alteração", key="btn_save_edit_amb"):
            supabase.table("ambientes").update({"nome": novo_nome}).eq("id", amb["id"]).execute()
            
            st.success("Atualizado!")
            # Limpa o cache após edição
            st.cache_data.clear()
            del st.session_state["edit_ambiente"]
            st.rerun()

with aba3:

    st.header("📦 Editar Materiais")

    # 1. Inicializa o contador de reset para Materiais se não existir
    if "reset_mat_count" not in st.session_state:
        st.session_state.reset_mat_count = 0

    # -------------------------
    # CRIAR MATERIAL
    # -------------------------
    # 2. Gera a chave dinâmica baseada no contador
    chave_material = f"input_novo_material_{st.session_state.reset_mat_count}"
    
    novo_material = st.text_input("Novo material", key=chave_material)

    if st.button("Adicionar", key="btn_add_material"):
        if not novo_material:
            st.warning("Digite o nome do material")
        else:
            nome_limpo = novo_material.strip()
            
            # Verifica se já existe no banco
            existe = supabase.table("materiais").select("*").eq("nome", nome_limpo).execute().data

            if existe:
                st.warning("Material já existe")
            else:
                try:
                    supabase.table("materiais").insert({"nome": nome_limpo}).execute()
                    st.success(f"✅ Material '{nome_limpo}' criado!")
                    
                    # 3. O TRUQUE: Aumenta o contador para resetar o input no próximo rerun
                    st.session_state.reset_mat_count += 1
                    
                    # LIMPA O CACHE para a Aba 4 enxergar o novo material
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar material: {e}")

    st.markdown("---")
    
    # -------------------------
    # BUSCA E LISTAGEM
    # -------------------------
    busca_material = st.text_input("🔎 Buscar material", key="busca_material")

    # Buscamos a lista atualizada
    materiais = supabase.table("materiais").select("*").order("nome").execute().data

    if busca_material:
        materiais = [m for m in materiais if busca_material.lower() in m["nome"].lower()]

    if not materiais:
        st.info("Nenhum material cadastrado.")
    else:
        for m in materiais:
            col1, col2, col3 = st.columns([6,1,1])
            with col1:
                st.write(m["nome"])
            with col2:
                if st.button("✏️", key=f"edit_mat_{m['id']}"):
                    st.session_state["edit_material"] = m
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_mat_{m['id']}"):
                    st.session_state["confirm_delete_material"] = m
                    st.rerun()

    # -------------------------
    # MODAL DE CONFIRMAR EXCLUSÃO
    # -------------------------
    if "confirm_delete_material" in st.session_state:
        mat = st.session_state["confirm_delete_material"]
        st.error(f"⚠️ Atenção! Excluir '{mat['nome']}' apagará todos os itens vinculados a ele.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, excluir material", key="conf_del_def"):
                try:
                    # 1. Deleta itens vinculados (Foreign Key)
                    supabase.table("itens_inventario").delete().eq("material_id", mat["id"]).execute()
                    # 2. Deleta o material
                    supabase.table("materiais").delete().eq("id", mat["id"]).execute()
                    
                    st.success("Material e itens removidos!")
                    st.cache_data.clear() # ATUALIZA O CACHE
                    del st.session_state["confirm_delete_material"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
        with col2:
            if st.button("Cancelar", key="canc_del_def"):
                del st.session_state["confirm_delete_material"]
                st.rerun()

    # -------------------------
    # MODAL DE EDITAR MATERIAL
    # -------------------------
    if "edit_material" in st.session_state:
        mat = st.session_state["edit_material"]
        st.subheader("✏️ Editar Material")
        
        novo_nome = st.text_input("Novo nome", value=mat["nome"], key="edit_nome_mat_input")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar alteração", key="save_edit_mat_btn"):
                if not novo_nome:
                    st.warning("Nome não pode ser vazio")
                else:
                    supabase.table("materiais").update({"nome": novo_nome.strip()}).eq("id", mat["id"]).execute()
                    st.success("Atualizado!")
                    st.cache_data.clear() # ATUALIZA O CACHE
                    del st.session_state["edit_material"]
                    st.rerun()
        with c2:
            if st.button("Sair sem salvar", key="cancel_edit_mat_btn"):
                del st.session_state["edit_material"]
                st.rerun()


with aba4:
    st.header("📋 Controle de materiais")

    # 1. BUSCA DE DADOS (Cache)
    unidades = get_unidades()
    materiais_db = get_materiais()
    ambientes_all = get_ambientes()
    itens_all = get_itens()

    # =========================
    # ÁREA DE CADASTRO
    # =========================
    st.subheader("➕ Cadastrar Item")

    unidade_sel = st.selectbox(
        "Unidade", unidades, format_func=lambda x: x["nome"],
        index=None, placeholder="Selecione a unidade...", key="item_unidade"
    )

    if unidade_sel:
        ambientes_f = [a for a in ambientes_all if a["unidade_id"] == unidade_sel["id"]]
        
        ambiente_sel = st.selectbox(
            "Ambiente", ambientes_f, format_func=lambda x: x["nome"],
            index=None, placeholder="Selecione o ambiente...", key="item_ambiente"
        )

        if ambiente_sel:
            lista_materiais = materiais_db + [{"id": "outro", "nome": "Outro..."}]
            material_sel = st.selectbox(
                "Material", lista_materiais, format_func=lambda x: x["nome"],
                index=None, placeholder="Selecione o material...", key="item_material"
            )

            novo_material = None
            if material_sel and material_sel["id"] == "outro":
                novo_material = st.text_input("Nome do novo material", key="novo_mat_item")

            patrimonio = st.text_input("Patrimônio", key="patrimonio_item")
            obs_item = st.text_area("Observações", key="obs_item")
            status = st.selectbox(
                "Status", ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"],
                index=0, key="status_item"
            )

            if st.button("Salvar Item", key="btn_salvar_item"):
                material_id = None 
                
                if material_sel and material_sel["id"] == "outro":
                    if not novo_material:
                        st.warning("⚠️ Digite o nome do novo material")
                        st.stop()
                    else:
                        res_mat = supabase.table("materiais").insert({"nome": novo_material.strip()}).execute()
                        if res_mat.data:
                            material_id = res_mat.data[0]["id"]
                            st.cache_data.clear()
                elif material_sel:
                    material_id = material_sel["id"]

                if material_id and ambiente_sel:
                    try:
                        res_item = supabase.table("itens_inventario").insert({
                            "ambiente_id": ambiente_sel["id"],
                            "material_id": material_id,
                            "patrimonio": patrimonio,
                            "status": status,
                            "observacao": obs_item
                        }).execute()
                
                        if res_item.data:
                            id_novo = res_item.data[0]["id"]
                            # Auditoria Inicial
                            supabase.table("historico_alteracoes").insert({
                                "item_id": id_do_item,
                                "usuario": st.session_state.nome_admin, # <--- Aqui entra o nome de quem logou
                                "detalhes": f"Ação realizada por {st.session_state.nome_admin} em {datetime.now().strftime('%d/%m %H:%M')}"
                            }).execute()
                
                            st.success("✅ Item cadastrado!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {e}")
    else:
        st.info("Selecione uma unidade acima para realizar um novo cadastro.")

    st.markdown("---")
    st.subheader("🔎 Consulta e Auditoria")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        f_unidade = st.selectbox("Filtrar Unidade", ["Todas"] + [u["nome"] for u in unidades], key="f_uni_tree")
    with col2:
        f_material = st.text_input("Material", key="f_mat_tree")
    with col3:
        f_status = st.selectbox("Status", ["Todos", "satisfatorio", "trocar_nao_urgente", "trocar_urgente"], key="f_sta_tree")

    dict_amb = {a["id"]: a for a in ambientes_all}
    dict_mat = {m["id"]: m for m in materiais_db}
    dict_uni = {u["id"]: u for u in unidades}

    estrutura = {}
    for item in itens_all:
        amb = dict_amb.get(item["ambiente_id"], {})
        mat = dict_mat.get(item["material_id"], {})
        uni = dict_uni.get(amb.get("unidade_id"), {})

        if f_unidade != "Todas" and uni.get("nome") != f_unidade: continue
        if f_material and f_material.lower() not in mat.get("nome", "").lower(): continue
        if f_status != "Todos" and item["status"] != f_status: continue

        u_nome, a_nome = uni.get("nome", "Sem unidade"), amb.get("nome", "Sem ambiente")
        estrutura.setdefault(u_nome, {}).setdefault(a_nome, []).append({**item, "mat_nome": mat.get("nome", "Desconhecido")})

    if not estrutura:
        st.info("Nenhum item encontrado.")
    else:
        # Percorremos as Unidades
        for unidade, ambientes_dict in estrutura.items():
            
            # 1. CÁLCULO DE TOTAIS DA UNIDADE
            qtd_ambientes = len(ambientes_dict)
            qtd_itens_total = sum(len(lista) for lista in ambientes_dict.values())
            
            # Título com contagem: 🏥 USF Exemplo (Ambientes: 3 | Itens: 12)
            titulo_unidade = f"🏥 {unidade} (Ambientes: {qtd_ambientes} / Itens: {qtd_itens_total})"
            
            # Mudamos 'expanded=True' para 'False' para não poluir
            with st.expander(titulo_unidade, expanded=False):
                
                # Percorremos os Ambientes desta Unidade
                for ambiente, itens_lista in ambientes_dict.items():
                    
                    # 2. CÁLCULO DE ITENS DO AMBIENTE
                    qtd_itens_amb = len(itens_lista)
                    
                    # Título do Ambiente: 📍 Consultório 1 (Itens: 5)
                    titulo_ambiente = f"📍 {ambiente} ({qtd_itens_amb} itens)"
                    
                    with st.expander(titulo_ambiente, expanded=False):
                        for i in itens_lista:
                        # --- O resto do seu código de botões (Editar, Deletar, Histórico) entra aqui ---
                            item_container = st.container()
                            
                            col_txt, col_edit, col_del, col_aud = item_container.columns([5,1,1,1])
                            
                            with col_txt:
                                st.write(f"{cor(i['status'])} **{i['mat_nome']}** | Pat: {i['patrimonio']}")
                                if i.get("observacao"): st.caption(f"📝 {i['observacao']}")

                            with col_edit:
                                if st.button("✏️", key=f"btn_ed_{i['id']}"):
                                    st.session_state["edit_item_id"] = i["id"]
                                    st.rerun()
                            
                            with col_del:
                                if st.button("🗑️", key=f"btn_del_{i['id']}"):
                                    st.session_state["confirm_delete_item_id"] = i["id"]
                                    st.rerun()

                            with col_aud:
                                if st.button("📜", key=f"btn_aud_{i['id']}"):
                                    st.session_state["view_audit_id"] = i["id"]
                                    st.rerun()

                            # --- RENDERIZAÇÃO DOS MODAIS DENTRO DO ITEM ---
                            
                            # 1. HISTÓRICO
                            if st.session_state.get("view_audit_id") == i["id"]:
                                with st.container(border=True):
                                    st.info(f"Histórico: {i['mat_nome']}")
                                    
                                    # Chamada segura ao banco (sem .order() para não causar APIError)
                                    res = supabase.table("historico_alteracoes").select("*").eq("item_id", i["id"]).execute()
                                    logs = res.data
                                    
                                    if logs:
                                        # Ordenamos via Python para garantir que o mais novo fique em cima
                                        logs = sorted(logs, key=lambda x: x.get('created_at', ''), reverse=True)
                                        
                                        for l in logs:
                                            # Pegamos o 'created_at' ou 'data_alteracao'
                                            raw_date = l.get('created_at') or l.get('data_alteracao')
                                            
                                            if raw_date:
                                                try:
                                                    # Limpa a string de data (remove milissegundos e fuso se necessário)
                                                    clean_date = raw_date.split('.')[0].replace('T', ' ')
                                                    dt_obj = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
                                                    dt_f = dt_obj.strftime('%d/%m/%Y %H:%M')
                                                except Exception:
                                                    dt_f = raw_date # Se falhar, mostra o que veio do banco
                                            else:
                                                dt_f = "Data Indisponível"
                            
                                            st.write(f"⏰ **{dt_f}** | {l['detalhes']}")
                                    else:
                                        st.write("Sem registros.")
                                    
                                    if st.button("Fechar Histórico", key=f"cls_aud_{i['id']}"):
                                        del st.session_state["view_audit_id"]
                                        st.rerun()

                            # --- 2. EDIÇÃO (Versão com Histórico de Observações) ---
                            if st.session_state.get("edit_item_id") == i["id"]:
                                with st.container(border=True):
                                    st.markdown("### ✏️ Editar")
                                    n_pat = st.text_input("Patrimônio", value=i["patrimonio"], key=f"inp_pat_{i['id']}")
                                    # Troquei para text_area para facilitar a escrita de notas longas
                                    n_obs = st.text_area("Observação", value=i.get("observacao", "") or "", key=f"inp_obs_{i['id']}")
                                    
                                    st_opts = ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"]
                                    n_sta = st.selectbox("Status", st_opts, index=st_opts.index(i["status"]) if i["status"] in st_opts else 0, key=f"inp_sta_{i['id']}")
                                    
                                    c1, c2 = st.columns(2)
                                    if c1.button("Salvar", key=f"sv_{i['id']}"):
                                        # Lógica para detectar o que mudou
                                        mudancas = []
                                        if n_sta != i["status"]:
                                            mudancas.append(f"Status: {i['status']} ➔ {n_sta}")
                                        if n_pat != i["patrimonio"]:
                                            mudancas.append(f"Pat: {i['patrimonio']} ➔ {n_pat}")
                                        
                                        obs_atual = i.get("observacao") or ""
                                        if n_obs != obs_atual:
                                            mudancas.append(f"Obs: {n_obs if n_obs else '(vazia)'}")
                            
                                        # Só executa se houver algo na lista de mudanças
                                        if mudancas:
                                            detalhes_log = " | ".join(mudancas)
                                            
                                            # Grava no histórico
                                            supabase.table("historico_alteracoes").insert({
                                                "item_id": i["id"], 
                                                "usuario": "Admin", 
                                                "detalhes": detalhes_log
                                            }).execute()
                                            
                                            # Atualiza o item
                                            supabase.table("itens_inventario").update({
                                                "patrimonio": n_pat, 
                                                "status": n_sta, 
                                                "observacao": n_obs
                                            }).eq("id", i["id"]).execute()
                                            
                                            st.success("✅ Alterações salvas!")
                                            st.cache_data.clear()
                                            del st.session_state["edit_item_id"]
                                            st.rerun()
                                        else:
                                            st.warning("Nenhuma alteração foi feita.")
                            
                                    if c2.button("Cancelar", key=f"cn_{i['id']}"):
                                        del st.session_state["edit_item_id"]
                                        st.rerun()

                            # 3. EXCLUSÃO
                            if st.session_state.get("confirm_delete_item_id") == i["id"]:
                                with st.container(border=True):
                                    st.error("Excluir item?")
                                    if st.button("Confirmar", key=f"v_del_{i['id']}"):
                                        supabase.table("historico_alteracoes").delete().eq("item_id", i["id"]).execute()
                                        supabase.table("itens_inventario").delete().eq("id", i["id"]).execute()
                                        st.cache_data.clear()
                                        del st.session_state["confirm_delete_item_id"]
                                        st.rerun()
                                    if st.button("Desistir", key=f"n_del_{i['id']}"):
                                        del st.session_state["confirm_delete_item_id"]
                                        st.rerun()
with aba5:
    st.subheader("📊 Relatórios")
    
    if estrutura:
        # 1. Preparar os dados para o Excel
        dados_excel = []
        
        for unidade, ambientes_dict in estrutura.items():
            # Linha da Unidade
            dados_excel.append({
                "Hierarquia": f"🏥 UNIDADE: {unidade.upper()}", 
                "Status": "", 
                "Patrimônio": "", 
                "Observação": ""
            })
            
            for ambiente, itens_lista in ambientes_dict.items():
                # Linha do Ambiente
                dados_excel.append({
                    "Hierarquia": f"  📍 {ambiente}", 
                    "Status": "", 
                    "Patrimônio": "", 
                    "Observação": ""
                })
                
                for i in itens_lista:
                    # Linha do Item
                    dados_excel.append({
                        "Hierarquia": f"      - {i['mat_nome']}",
                        "Status": i['status'],
                        "Patrimônio": i['patrimonio'],
                        "Observação": i.get('observacao', '')
                    })
        
        df_export = pd.DataFrame(dados_excel)
    
        # 2. Criar o arquivo Excel em memória
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Inventario')
            
            workbook  = writer.book
            worksheet = writer.sheets['Inventario']
    
            # Formatos visuais
            fmt_unidade = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            fmt_ambiente = workbook.add_format({'bold': True, 'bg_color': '#EAF1DD', 'italic': True})
            
            # Ajustar largura das colunas
            worksheet.set_column('A:A', 50)
            worksheet.set_column('B:D', 20)
    
            # Aplicar formatação nas linhas (começa em 1 porque 0 é o cabeçalho)
            for row_num, data in enumerate(dados_excel):
                if "🏥 UNIDADE:" in data["Hierarquia"]:
                    worksheet.set_row(row_num + 1, None, fmt_unidade)
                elif "📍" in data["Hierarquia"]:
                    worksheet.set_row(row_num + 1, None, fmt_ambiente)
    
        # 3. Botão de Download (O segredo é o buffer.getvalue())
        st.download_button(
            label="📥 Baixar Inventário Atualizado (Excel)",
            data=buffer.getvalue(),
            file_name=f"Inventario_USF_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Não há dados filtrados para exportar.")
