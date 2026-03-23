import pandas as pd
import io
import streamlit as st
import time
from supabase import create_client
from datetime import datetime, timedelta
import bcrypt
import extra_streamlit_components as stx

st.set_page_config(
    page_title="Comissão de Materiais", # Nome que aparece na aba do navegador
    page_icon="🏥",                          # Emoji ou link de uma imagem para o ícone
    layout="wide"                            # Opcional: faz o app usar a tela toda
)

# 1. Configurações de conexão
url = "https://oudfbraxmwuskdnnlisf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91ZGZicmF4bXd1c2tkbm5saXNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4Nzc5NzQsImV4cCI6MjA4OTQ1Mzk3NH0.QnL67maBxqsfgm4xHmLBYcqPbQ99swjHw3OzndSM9qA"
supabase = create_client(url, key)

# --- 2. INICIALIZAÇÃO DE SEGURANÇA E COOKIES ---

# 1. Instancia o manager APENAS UMA VEZ
cookie_manager = stx.CookieManager(key="cookie_manager_global")

# 2. Inicialização global das variáveis de estado
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "nome_admin" not in st.session_state:
    st.session_state.nome_admin = ""

# --- 3. LÓGICA DE PERSISTÊNCIA REFORÇADA ---

# Pegamos os cookies
cookies = cookie_manager.get_all()

# Se o componente ainda está carregando (retorna None), paramos o script aqui 
# e esperamos o próximo ciclo automático (que acontece em milissegundos)
if cookies is None:
    st.info("Carregando sistema segura...")
    st.stop()

# Se o usuário não está logado no Session State, mas existe o cookie no navegador:
if st.session_state.usuario_logado is None and "usuario_logado" in cookies:
    usuario_id = cookies["usuario_logado"]
    if usuario_id:
        try:
            res = supabase.table("usuarios").select("usuario, nome_exibicao").eq("usuario", usuario_id).execute()
            if res.data:
                st.session_state.usuario_logado = res.data[0]["usuario"]
                st.session_state.nome_admin = res.data[0]["nome_exibicao"]
                st.rerun()
        except:
            pass

# --- 4. FUNÇÕES DE INTERFACE ---



def verificar_hash(senha, hash_db):
    return bcrypt.checkpw(senha.encode('utf-8'), hash_db.encode('utf-8'))

def tela_login():
    if st.session_state.usuario_logado is None:
        _, col2, _ = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🏥 Controle de Materiais - Login")
            with st.container(border=True):
                input_user = st.text_input("Matrícula", key="login_user_input")
                input_pass = st.text_input("Senha", type="password", key="login_pass_input")
                
                if st.button("Acessar Sistema", use_container_width=True):
                    # Login Admin Master
                    if input_user == "admin" and input_pass == "1234":
                        st.session_state.usuario_logado = "admin"
                        st.session_state.nome_admin = "Administrador Master"
                        cookie_manager.set("usuario_logado", "admin", expires_at=datetime.now() + timedelta(days=7))
                        time.sleep(0.2) # Pequeno delay para garantir a gravação do cookie
                        st.rerun()
                    # Login Supabase
                    else:
                        res = supabase.table("usuarios").select("*").eq("usuario", input_user).execute()
                        if res.data and verificar_hash(input_pass, res.data[0]["senha_hash"]):
                            u = res.data[0]
                            st.session_state.usuario_logado = u["usuario"]
                            st.session_state.nome_admin = u["nome_exibicao"]
                            cookie_manager.set("usuario_logado", u["usuario"], expires_at=datetime.now() + timedelta(days=7))
                            time.sleep(0.2)
                            st.rerun()
                        else:
                            st.error("Usuário ou senha inválidos.")
        st.stop()

def sidebar_usuario():
    if st.session_state.get("usuario_logado"):
        st.sidebar.markdown(f"👤 **{st.session_state.nome_admin}**")
        
        # Usamos uma chave (key) única para evitar conflitos de renderização
        if st.sidebar.button("Sair", key="btn_logout_sidebar"):
            # 1. Limpa os Cookies (Opcional: Verifique se o cookie_manager está ok)
            try:
                cookie_manager.delete("usuario_logado")
            except:
                pass
            
            # 2. LIMPEZA TOTAL do Session State (Isso é o que garante o logout)
            # Em vez de setar para None, limpamos para o app resetar as abas
            st.session_state.usuario_logado = None
            st.session_state.nome_admin = ""
            
            # 3. Feedback visual e reinicialização
            st.sidebar.success("Saindo...")
            time.sleep(0.5) # Aumentamos um pouco para o navegador processar o cookie.delete
            st.rerun()

# --- 5. EXECUÇÃO ---
tela_login()
sidebar_usuario()

# O RESTANTE DO SEU CÓDIGO (Abas, etc) CONTINUA AQUI...




def gerar_senha_inicial(senha_numerica):
    hash_gerado = bcrypt.hashpw(str(senha_numerica).encode('utf-8'), bcrypt.gensalt())
    return hash_gerado.decode('utf-8')

def verificar_hash(senha, hash_db):
    return bcrypt.checkpw(senha.encode('utf-8'), hash_db.encode('utf-8'))

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
    st.header("📋 Controle de Materiais")

    # --- 1. BUSCA DE DADOS (Cache - Mantido) ---
    unidades = get_unidades()
    materiais_db = get_materiais()
    ambientes_all = get_ambientes()
    itens_all = get_itens()

    # =========================================================
    # ÁREA DE CADASTRO (Otimizada para Velocidade Máxima)
    # =========================================================
st.subheader("➕ Cadastrar Novo Item")
    
    # 1. Selectboxes de hierarquia (fora do form)
    c1, c2 = st.columns(2)
    unidade_sel = c1.selectbox(
        "1. Selecione a Unidade", unidades, format_func=lambda x: x["nome"],
        index=None, placeholder="Escolha a unidade...", key="item_unidade"
    )

    if unidade_sel:
        ambientes_f = [a for a in ambientes_all if a["unidade_id"] == unidade_sel["id"]]
        ambiente_sel = c2.selectbox(
            "2. Selecione o Ambiente", ambientes_f, format_func=lambda x: x["nome"],
            index=None, placeholder="Escolha o ambiente...", key="item_ambiente"
        )

        if ambiente_sel:
            # Formulário para detalhes
            with st.form("form_cadastro_detalhes", clear_on_submit=True):
                st.markdown("##### 3. Detalhes do Item")
                
                col_mat, col_pat = st.columns([3, 1])
                lista_materiais = materiais_db + [{"id": "outro", "nome": "Outro..."}]
                material_sel = col_mat.selectbox(
                    "Material", lista_materiais, format_func=lambda x: x["nome"],
                    index=None, placeholder="Selecione..."
                )
                
                novo_material = st.text_input("Se selecionou 'Outro', digite o nome:", placeholder="Nome do novo material...")
                patrimonio = col_pat.text_input("Patrimônio", placeholder="Ex: 123456")
                obs_item = st.text_area("Observações (opcional)", placeholder="Detalhes adicionais...")
                
                status = st.selectbox(
                    "Status Inicial", ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"], index=0
                )

                btn_salvar = st.form_submit_button("✅ Salvar Item no Inventário", use_container_width=True)

                if btn_salvar:
                    with st.spinner("Salvando..."):
                        try:
                            # Lógica do Material
                            if material_sel and material_sel["id"] != "outro":
                                material_id = material_sel["id"]
                            elif material_sel and material_sel["id"] == "outro" and novo_material:
                                res_mat = supabase.table("materiais").upsert({"nome": novo_material.strip()}, on_conflict="nome").execute()
                                material_id = res_mat.data[0]["id"]
                            else:
                                st.error("⚠️ Selecione um material ou digite o nome do novo.")
                                st.stop()

                            # Gravação do Item
                            res_item = supabase.table("itens_inventario").insert({
                                "ambiente_id": ambiente_sel["id"],
                                "material_id": material_id,
                                "patrimonio": patrimonio,
                                "status": status,
                                "observacao": obs_item
                            }).execute()
                        
                            if res_item.data:
                                id_criado = res_item.data[0]["id"]
                                supabase.table("historico_alteracoes").insert({
                                    "item_id": id_criado,
                                    "usuario": st.session_state.get("nome_admin", "Sistema"),
                                    "detalhes": "Cadastro inicial"
                                }).execute()
                        
                                st.toast("✅ Item salvo!", icon='🚀')
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Erro crítico: {e}")
    else:
        st.info("💡 Selecione uma unidade acima para liberar o formulário de cadastro.")

    st.markdown("---")

    # =========================================================
    # ÁREA DE CONSULTA (Pré-processamento Eficiente)
    # =========================================================
    st.subheader("🔎 Consulta")
    
    # Filtros visuais agradáveis
    c1, c2, c3 = st.columns(3)
    f_unidade = c1.selectbox("Filtrar Unidade", ["Todas"] + [u["nome"] for u in unidades], key="f_uni_tree")
    f_material = c2.text_input("Buscar Material (Nome)", key="f_mat_tree", placeholder="Digite parte do nome...")
    f_status = c3.selectbox("Filtrar Status", ["Todos", "satisfatorio", "trocar_nao_urgente", "trocar_urgente"], key="f_sta_tree")

    # --- Otimização Técnica: Dicionários para busca instantânea O(1) ---
    dict_amb = {a["id"]: a for a in ambientes_all}
    dict_mat = {m["id"]: m for m in materiais_db}
    dict_uni = {u["id"]: u for u in unidades}

    # Pré-filtragem centralizada (Evita processamento extra na renderização)
    estrutura = {}
    for item in itens_all:
        amb = dict_amb.get(item["ambiente_id"], {})
        mat = dict_mat.get(item["material_id"], {})
        uni = dict_uni.get(amb.get("unidade_id"), {})

        # Aplicação dos filtros
        if f_unidade != "Todas" and uni.get("nome") != f_unidade: continue
        if f_material and f_material.lower() not in mat.get("nome", "").lower(): continue
        if f_status != "Todos" and item["status"] != f_status: continue

        u_nome = uni.get("nome", "Sem unidade")
        a_nome = amb.get("nome", "Sem ambiente")
        
        # Montagem da árvore de exibição
        if u_nome not in estrutura: estrutura[u_nome] = {}
        if a_nome not in estrutura[u_nome]: estrutura[u_nome][a_nome] = []
        
        # Adiciona nome do material ao item para exibição
        item_completo = {**item, "mat_nome": mat.get("nome", "Desconhecido")}
        estrutura[u_nome][a_nome].append(item_completo)

    # --- RENDERIZAÇÃO VISUAL AGRADÁVEL ---
    if not estrutura:
        st.info("Nenhum item corresponde aos filtros selecionados.")
    else:
        # Árvore Hierárquica
        for unidade, ambientes_dict in estrutura.items():
            # Cálculos de totais
            qtd_ambientes = len(ambientes_dict)
            qtd_itens_uni = sum(len(lista) for lista in ambientes_dict.values())
            
            # Título da Unidade Compacto e Informativo
            label_uni = f"🏥 {unidade} ({qtd_ambientes} Amb / {qtd_itens_uni} Itens)"
            with st.expander(label_uni, expanded=False):
                
                for ambiente, itens_lista in ambientes_dict.items():
                    qtd_itens_amb = len(itens_lista)
                    
                    # Título do Ambiente
                    label_amb = f"📍 {ambiente} ({qtd_itens_amb} itens)"
                    with st.expander(label_amb, expanded=False):
                        
                        # Listagem de Itens Otimizada
                        for i in itens_lista:
                            # Container para agrupar visualmente o item e suas ações
                            item_box = st.container()
                            col_txt, col_acoes = item_box.columns([5, 1.2]) # Espaço ajustado para ações
                            
                            with col_txt:
                                # Função cor(status) mantida
                                st.write(f"{cor(i['status'])} **{i['mat_nome']}** | Pat: `{i['patrimonio']}`")
                                if i.get("observacao"): 
                                    st.caption(f"📝 {i['observacao']}")
                                    
                            with col_acoes:
                                # 1. A ENGRENAGEM (Só aparece se nenhum modo de edição/exclusão estiver aberto para este item)
                                # Isso evita que o usuário abra o menu enquanto já está excluindo
                                if not (st.session_state.get("confirm_delete_item_id") == i["id"] or 
                                        st.session_state.get("edit_item_id") == i["id"] or
                                        st.session_state.get("view_audit_id") == i["id"]):
                                    
                                    with st.popover("⚙️", help="Ações"):
                                        st.write(f"**Opções:** {i['mat_nome']}")
                                        
                                        if st.button("✏️ Editar", key=f"btn_ed_{i['id']}", use_container_width=True):
                                            st.session_state["edit_item_id"] = i["id"]
                                            st.rerun() # O rerun fecha o popover e limpa a tela para mostrar a edição
                                            
                                        if st.button("📜 Histórico", key=f"btn_aud_{i['id']}", use_container_width=True):
                                            st.session_state["view_audit_id"] = i["id"]
                                            st.rerun()
                                            
                                        st.markdown("---")
                                        if st.button("🗑️ Excluir", key=f"btn_del_{i['id']}", use_container_width=True, type="primary"):
                                            st.session_state["confirm_delete_item_id"] = i["id"]
                                            st.rerun() # O menu some e a tela de confirmação aparece "limpa" embaixo

                            # --- RENDERIZAÇÃO DOS MODAIS IN-LINE (Sua lógica mantida) ---
                            
                            # 1. HISTÓRICO
                            if st.session_state.get("view_audit_id") == i["id"]:
                                with st.container(border=True):
                                    st.info(f"Histórico de Alterações: {i['mat_nome']}")
                                    res = supabase.table("historico_alteracoes").select("*").eq("item_id", i["id"]).execute()
                                    logs = res.data
                                    if logs:
                                        # Ordenação Python (Mais eficiente que order no Supabase para poucos registros)
                                        logs = sorted(logs, key=lambda x: x.get('created_at', ''), reverse=True)
                                        for l in logs:
                                            # Lógica de formatação de data mantida
                                            raw_date = l.get('created_at') or l.get('data_alteracao')
                                            if raw_date:
                                                try:
                                                    clean_date = raw_date.split('.')[0].replace('T', ' ')
                                                    dt_obj = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
                                                    dt_f = dt_obj.strftime('%d/%m/%Y %H:%M')
                                                except: dt_f = raw_date
                                            else: dt_f = "--/--/--"
                                            st.write(f"⏰ **{dt_f}** | {l['detalhes']}")
                                    else: st.write("Nenhum registro encontrado.")
                                    if st.button("Fechar Histórico", key=f"cls_aud_{i['id']}", use_container_width=True):
                                        del st.session_state["view_audit_id"]
                                        st.rerun()

                            # 2. EDIÇÃO
                            if st.session_state.get("edit_item_id") == i["id"]:
                                with st.container(border=True):
                                    st.markdown(f"### ✏️ Editar: {i['mat_nome']}")
                                    n_pat = st.text_input("Patrimônio", value=i["patrimonio"], key=f"inp_pat_{i['id']}")
                                    n_obs = st.text_area("Observação", value=i.get("observacao", "") or "", key=f"inp_obs_{i['id']}")
                                    st_opts = ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"]
                                    n_sta = st.selectbox("Status", st_opts, index=st_opts.index(i["status"]) if i["status"] in st_opts else 0, key=f"inp_sta_{i['id']}")
                                    
                                    c1, c2 = st.columns(2)
                                    if c1.button("Salvar Alterações", key=f"sv_{i['id']}", use_container_width=True):
                                        # Lógica de detecção de mudanças mantida
                                        mudancas = []
                                        if n_sta != i["status"]: mudancas.append(f"Status: {i['status']} ➔ {n_sta}")
                                        if n_pat != i["patrimonio"]: mudancas.append(f"Pat: {i['patrimonio']} ➔ {n_pat}")
                                        obs_atual = i.get("observacao") or ""
                                        if n_obs != obs_atual: mudancas.append(f"Obs Atualizada")
                            
                                        if mudancas:
                                            detalhes_log = " | ".join(mudancas)
                                            usuario_edicao = st.session_state.get("nome_admin", "Admin")
                                            supabase.table("historico_alteracoes").insert({
                                                "item_id": i["id"], "usuario": usuario_edicao, "detalhes": detalhes_log
                                            }).execute()
                                            supabase.table("itens_inventario").update({
                                                "patrimonio": n_pat, "status": n_sta, "observacao": n_obs
                                            }).eq("id", i["id"]).execute()
                                            st.success("✅ Alterações salvas!")
                                            st.cache_data.clear()
                                            del st.session_state["edit_item_id"]
                                            st.rerun()
                                        else: st.warning("Nenhuma alteração detectada.")
                                    if c2.button("Cancelar", key=f"cn_{i['id']}", use_container_width=True):
                                        del st.session_state["edit_item_id"]
                                        st.rerun()

                            # 3. EXCLUSÃO
                            if st.session_state.get("confirm_delete_item_id") == i["id"]:
                                with st.container(border=True):
                                    st.error(f"⚠️ Tem certeza que deseja excluir o item '{i['mat_nome']}'?")
                                    st.caption("Esta ação não pode ser desfeita e removerá todo o histórico associado.")
                                    col_v, col_n = st.columns(2)
                                    if col_v.button("Sim, Excluir permanentemente", key=f"v_del_{i['id']}", use_container_width=True):
                                        # Deleta histórico primeiro (FK constraint)
                                        supabase.table("historico_alteracoes").delete().eq("item_id", i["id"]).execute()
                                        supabase.table("itens_inventario").delete().eq("id", i["id"]).execute()
                                        st.cache_data.clear()
                                        del st.session_state["confirm_delete_item_id"]
                                        st.rerun()
                                    if col_n.button("Não, Cancelar", key=f"n_del_{i['id']}", use_container_width=True):
                                        del st.session_state["confirm_delete_item_id"]
                                        st.rerun()
                            
                            # Divisor visual leve entre itens
                            st.markdown("<hr style='margin: 0.5em 0; border-color: #f0f2f6;'>", unsafe_allow_html=True)


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
