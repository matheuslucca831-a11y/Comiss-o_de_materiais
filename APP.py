

import streamlit as st
from supabase import create_client

url = "https://oudfbraxmwuskdnnlisf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91ZGZicmF4bXd1c2tkbm5saXNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4Nzc5NzQsImV4cCI6MjA4OTQ1Mzk3NH0.QnL67maBxqsfgm4xHmLBYcqPbQ99swjHw3OzndSM9qA"

supabase = create_client(url, key)

from datetime import datetime, timedelta

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







aba1, aba2, aba3, aba4 = st.tabs([
    "Unidades",
    "Ambientes",
    "Editar Materiais",
    "Controle de Materiais"
])


with aba1:
    st.header("🏥 Unidades")

    # 1. CARREGAMENTO DOS DADOS VIA CACHE
    unidades_data = get_unidades()

    # -------------------------
    # CRIAR UNIDADE
    # -------------------------
    nome_unidade = st.text_input("Nome da unidade", key="input_create_unidade")

    if st.button("Criar Unidade", key="btn_create_unidade"):

        if not nome_unidade:
            st.warning("Digite o nome da unidade")
        else:
            # Verifica se existe usando os dados que já temos no cache (evita consulta ao banco)
            existe = [u for u in unidades_data if u["nome"].lower() == nome_unidade.lower()]

            if existe:
                st.warning("Unidade já existe")
            else:
                supabase.table("unidades").insert({
                    "nome": nome_unidade
                }).execute()

                st.success("Unidade criada!")
                # Limpa o cache para que a nova unidade apareça na listagem
                st.cache_data.clear()
                st.rerun()

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

    # -------------------------
    # BUSCAR UNIDADE (USANDO CACHE)
    # -------------------------
    busca_unidade = st.text_input("🔎 Buscar unidade", key="busca_unidade_amb")

    # Usando a função cacheadas em vez de query direta
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

        nome_ambiente = st.text_input("Nome do ambiente", key="input_nome_amb")

        if st.button("Criar Ambiente"):
            if not nome_ambiente:
                st.warning("Digite o nome do ambiente")
            else:
                supabase.table("ambientes").insert({
                    "nome": nome_ambiente,
                    "unidade_id": unidade_sel["id"]
                }).execute()

                st.success("Ambiente criado!")
                # Limpa o cache para atualizar a lista de ambientes abaixo
                st.cache_data.clear()
                st.rerun()

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

    # -------------------------
    # CRIAR MATERIAL
    # -------------------------
    novo_material = st.text_input("Novo material", key="input_novo_material")

    if st.button("Adicionar", key="btn_add_material"):

        if not novo_material:
            st.warning("Digite o nome do material")
        else:
            existe = supabase.table("materiais") \
                .select("*") \
                .eq("nome", novo_material) \
                .execute().data

            if existe:
                st.warning("Material já existe")
            else:
                supabase.table("materiais").insert({
                    "nome": novo_material
                }).execute()

                st.success("Material criado!")
                st.rerun()

    # -------------------------
    # BUSCA
    # -------------------------
    busca_material = st.text_input("🔎 Buscar material", key="busca_material")

    materiais = supabase.table("materiais").select("*").execute().data

    if busca_material:
        materiais = [m for m in materiais if busca_material.lower() in m["nome"].lower()]

    # -------------------------
    # LISTAGEM
    # -------------------------
    for m in materiais:
        col1, col2, col3 = st.columns([6,1,1])

        # Nome
        with col1:
            st.write(m["nome"])

        # Editar
        with col2:
            if st.button("✏️", key=f"edit_mat_{m['id']}"):
                st.session_state["edit_material"] = m

        # Deletar
        with col3:
            if st.button("🗑️", key=f"del_mat_{m['id']}"):
                st.session_state["confirm_delete_material"] = m

    # -------------------------
    # CONFIRMAR EXCLUSÃO
    # -------------------------
    if "confirm_delete_material" in st.session_state:

        mat = st.session_state["confirm_delete_material"]

        st.warning(f"O material '{mat['nome']}' pode estar vinculado a itens.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Sim, excluir"):

                try:
                    # deletar itens vinculados
                    supabase.table("itens_inventario") \
                        .delete() \
                        .eq("material_id", mat["id"]) \
                        .execute()

                    # deletar material
                    supabase.table("materiais") \
                        .delete() \
                        .eq("id", mat["id"]) \
                        .execute()

                    st.success("Material excluído!")
                    del st.session_state["confirm_delete_material"]
                    st.rerun()

                except Exception as e:
                    st.error("Erro:")
                    st.write(e)

        with col2:
            if st.button("Cancelar"):
                del st.session_state["confirm_delete_material"]
                st.rerun()

    # -------------------------
    # EDITAR MATERIAL
    # -------------------------
    if "edit_material" in st.session_state:

        mat = st.session_state["edit_material"]

        st.subheader("✏️ Editar Material")

        novo_nome = st.text_input(
            "Novo nome",
            value=mat["nome"],
            key="edit_nome_material"
        )

        if st.button("Salvar alteração", key="btn_salvar_material"):

            if not novo_nome:
                st.warning("Digite o nome")
            else:
                supabase.table("materiais") \
                    .update({"nome": novo_nome}) \
                    .eq("id", mat["id"]) \
                    .execute()

                st.success("Material atualizado!")
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
                if material_sel["id"] == "outro":
                    if not novo_material:
                        st.warning("Digite o nome do material")
                    else:
                        res_mat = supabase.table("materiais").insert({"nome": novo_material}).execute()
                        material_id = res_mat.data[0]["id"]
                else:
                    material_id = material_sel["id"]

                if material_id:
                    # 1. Insere o item e pega o ID gerado (res.data[0])
                    res_item = supabase.table("itens_inventario").insert({
                        "ambiente_id": ambiente_sel["id"],
                        "material_id": material_id,
                        "patrimonio": patrimonio,
                        "status": status,
                        "observacao": obs_item
                    }).execute()
                    
                    # 2. Registra na AUDITORIA a criação
                    if res_item.data:
                        novo_id_item = res_item.data[0]["id"]
                        detalhe_criacao = f"📦 Item cadastrado no ambiente: {ambiente_sel['nome']}. Status inicial: {status}"
                        
                        supabase.table("historico_alteracoes").insert({
                            "item_id": novo_id_item,
                            "usuario": "Admin", # Aqui você pode usar st.session_state.usuario se tiver login
                            "detalhes": detalhe_criacao
                        }).execute()

                    st.success(f"Item {material_sel['nome']} cadastrado e registrado no histórico!")
                    
                    # Limpeza do formulário (como combinamos antes)
                    chaves_para_limpar = ["item_unidade", "item_ambiente", "item_material", "novo_mat_item", "patrimonio_item", "obs_item"]
                    for chave in chaves_para_limpar:
                        if chave in st.session_state: del st.session_state[chave]
                    
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("Selecione uma unidade acima para realizar um novo cadastro.")

    st.markdown("---")
    st.subheader("🔎 Consulta e Auditoria")
    
    # Filtros de consulta
    col1, col2, col3 = st.columns(3)
    with col1:
        f_unidade = st.selectbox("Filtrar Unidade", ["Todas"] + [u["nome"] for u in unidades], key="f_uni_tree")
    with col2:
        f_material = st.text_input("Material", key="f_mat_tree")
    with col3:
        f_status = st.selectbox("Status", ["Todos", "satisfatorio", "trocar_nao_urgente", "trocar_urgente"], key="f_sta_tree")

    # Mapeamentos para exibição
    dict_amb = {a["id"]: a for a in ambientes_all}
    dict_mat = {m["id"]: m for m in materiais_db}
    dict_uni = {u["id"]: u for u in unidades}

    # Organização da estrutura
    estrutura = {}
    for item in itens_all:
        amb = dict_amb.get(item["ambiente_id"], {})
        mat = dict_mat.get(item["material_id"], {})
        uni = dict_uni.get(amb.get("unidade_id"), {})

        if f_unidade != "Todas" and uni.get("nome") != f_unidade: continue
        if f_material and f_material.lower() not in mat.get("nome", "").lower(): continue
        if f_status != "Todos" and item["status"] != f_status: continue

        u_nome, a_nome = uni.get("nome", "Sem unidade"), amb.get("nome", "Sem ambiente")
        estrutura.setdefault(u_nome, {}).setdefault(a_nome, []).append({**item, "mat_nome": mat.get("nome")})

    # =========================
    # EXIBIÇÃO HIERÁRQUICA (UNIDADE > AMBIENTE > ITEM)
    # =========================
    if not estrutura:
        st.info("Nenhum item encontrado")
    else:
        for unidade, ambientes_dict in estrutura.items():
            # Nível 1: Unidade
            with st.expander(f"🏥 {unidade}", expanded=False):
                
                for ambiente, itens_lista in ambientes_dict.items():
                    # Nível 2: Ambiente (Dentro da Unidade)
                    with st.expander(f"📍 {ambiente}", expanded=False):
                        
                        # Nível 3: Itens (Dentro do Ambiente)
                        for i in itens_lista:
                            col_txt, col_edit, col_del, col_aud = st.columns([5,1,1,1])
                            
                            with col_txt:
                                st.write(f"{cor(i['status'])} **{i['mat_nome']}** | Pat: {i['patrimonio']}")
                                if i.get("observacao"):
                                    st.caption(f"📝 Obs: {i['observacao']}")

                            with col_edit:
                                if st.button("✏️", key=f"ed_{i['id']}"):
                                    st.session_state["edit_item_id"] = i["id"]
                            
                            with col_del:
                                if st.button("🗑️", key=f"del_item_{i['id']}"):
                                    st.session_state["confirm_delete_item_id"] = i["id"]

                            with col_aud:
                                if st.button("📜", key=f"aud_{i['id']}"):
                                    st.session_state["view_audit_id"] = i["id"]

                            # --- MODAL DE AUDITORIA (Dentro do item) ---
                            if st.session_state.get("view_audit_id") == i["id"]:
                                with st.container(border=True):
                                    st.info(f"Histórico de: {i['mat_nome']}")
                                    logs = supabase.table("historico_alteracoes").select("*").eq("item_id", i["id"]).order("data_alteracao", desc=True).execute().data
                                    if not logs: 
                                        st.write("Nenhuma alteração registrada.")
                                    for l in logs:
                                        data_formatada = formato_brasilia(l['data_alteracao'])
                                        st.write(f"⏰ {data_formatada} | {l['detalhes']}")
                                    
                                    if st.button("Fechar Histórico", key=f"close_aud_{i['id']}"):
                                        del st.session_state["view_audit_id"]
                                        st.rerun()

                            # --- LOGICA DE EDIÇÃO ---
                            if st.session_state.get("edit_item_id") == i["id"]:
                                with st.container(border=True):
                                    st.markdown("### ✏️ Editar")
                                    n_pat = st.text_input("Novo Patrimônio", value=i["patrimonio"], key=f"p_{i['id']}")
                                    n_obs = st.text_input("Nova Obs", value=i.get("observacao", ""), key=f"o_{i['id']}")
                                    n_sta = st.selectbox("Novo Status", ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"], 
                                                       index=["satisfatorio", "trocar_nao_urgente", "trocar_urgente"].index(i["status"]), key=f"s_{i['id']}")
                                    
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        if st.button("Salvar", key=f"save_ed_{i['id']}"):
                                            # Auditoria
                                            detalhes = f"Alterou Status: {i['status']} -> {n_sta}. Obs: {n_obs}"
                                            supabase.table("historico_alteracoes").insert({
                                                "item_id": i["id"],
                                                "usuario": "Admin", # Pode mudar pelo seu nome dps
                                                "detalhes": detalhes
                                            }).execute()
                                            # Update
                                            supabase.table("itens_inventario").update({
                                                "patrimonio": n_pat, "status": n_sta, "observacao": n_obs
                                            }).eq("id", i["id"]).execute()
                                            
                                            st.cache_data.clear()
                                            del st.session_state["edit_item_id"]
                                            st.rerun()
                                    with c2:
                                        if st.button("Cancelar", key=f"cancel_ed_{i['id']}"):
                                            del st.session_state["edit_item_id"]
                                            st.rerun()
                            
                            # --- LOGICA DE EXCLUSÃO ---
                            if st.session_state.get("confirm_delete_item_id") == i["id"]:
                                st.error(f"Confirmar exclusão de {i['mat_nome']}?")
                                if st.button("Confirmar Exclusão", key=f"btn_confirm_del_{i['id']}"):
                                    supabase.table("itens_inventario").delete().eq("id", i["id"]).execute()
                                    st.cache_data.clear()
                                    del st.session_state["confirm_delete_item_id"]
                                    st.rerun()
                                if st.button("Desistir", key=f"btn_cancel_del_{i['id']}"):
                                    del st.session_state["confirm_delete_item_id"]
                                    st.rerun()

