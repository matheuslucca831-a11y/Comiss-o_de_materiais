

import streamlit as st
from supabase import create_client

url = "https://oudfbraxmwuskdnnlisf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91ZGZicmF4bXd1c2tkbm5saXNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4Nzc5NzQsImV4cCI6MjA4OTQ1Mzk3NH0.QnL67maBxqsfgm4xHmLBYcqPbQ99swjHw3OzndSM9qA"

supabase = create_client(url, key)










aba1, aba2, aba3, aba4 = st.tabs([
    "Unidades",
    "Ambientes",
    "Materiais",
    "Itens"
])


with aba1:
    st.header("🏥 Unidades")

    # -------------------------
    # CRIAR UNIDADE
    # -------------------------
    nome_unidade = st.text_input("Nome da unidade")

    if st.button("Criar Unidade"):

        if not nome_unidade:
            st.warning("Digite o nome da unidade")

        else:
            existe = supabase.table("unidades") \
                .select("*") \
                .eq("nome", nome_unidade) \
                .execute().data

            if existe:
                st.warning("Unidade já existe")
            else:
                supabase.table("unidades").insert({
                    "nome": nome_unidade
                }).execute()

                st.success("Unidade criada!")
                st.rerun()

    # -------------------------
    # BUSCA
    # -------------------------
    busca = st.text_input("🔎 Buscar unidade")

    unidades = supabase.table("unidades").select("*").execute().data

    if busca:
        unidades = [u for u in unidades if busca.lower() in u["nome"].lower()]

    # -------------------------
    # LISTAGEM COM AÇÕES
    # -------------------------
    for u in unidades:
        col1, col2, col3 = st.columns([6,1,1])

        # Nome
        with col1:
            st.write(u["nome"])

        # Editar
        with col2:
            if st.button("✏️", key=f"edit_{u['id']}"):
                st.session_state["edit_unidade"] = u

        # Deletar (AGORA COM CONFIRMAÇÃO)
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
            if st.button("Sim, excluir tudo"):

                try:
                    # Buscar ambientes da unidade
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
                    del st.session_state["confirm_delete_unidade"]
                    st.rerun()

                except Exception as e:
                    st.error("Erro ao excluir:")
                    st.write(e)

        # CANCELAR
        with col2:
            if st.button("Cancelar"):
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
            value=unidade["nome"]
        )

        if st.button("Salvar alteração"):
            supabase.table("unidades") \
                .update({"nome": novo_nome}) \
                .eq("id", unidade["id"]) \
                .execute()

            st.success("Atualizado!")
            del st.session_state["edit_unidade"]
            st.rerun()

with aba2:
    st.header("🏢 Ambientes")

    # -------------------------
    # BUSCAR UNIDADE
    # -------------------------
    busca_unidade = st.text_input("🔎 Buscar unidade", key="busca_unidade_amb")

    unidades = supabase.table("unidades").select("*").execute().data

    if busca_unidade:
        unidades = [u for u in unidades if busca_unidade.lower() in u["nome"].lower()]

    if not unidades:
        st.warning("Nenhuma unidade encontrada")
    else:
        unidade_sel = st.selectbox(
            "Selecione a unidade",
            unidades,
            format_func=lambda x: x["nome"]
        )

        # -------------------------
        # CRIAR AMBIENTE
        # -------------------------
        st.subheader("➕ Novo Ambiente")

        nome_ambiente = st.text_input("Nome do ambiente")

        if st.button("Criar Ambiente"):

            if not nome_ambiente:
                st.warning("Digite o nome do ambiente")

            else:
                supabase.table("ambientes").insert({
                    "nome": nome_ambiente,
                    "unidade_id": unidade_sel["id"]
                }).execute()

                st.success("Ambiente criado!")
                st.rerun()

        # -------------------------
        # LISTAR AMBIENTES DA UNIDADE
        # -------------------------
        st.subheader("📋 Ambientes da unidade")

        ambientes = supabase.table("ambientes") \
            .select("*") \
            .eq("unidade_id", unidade_sel["id"]) \
            .execute().data

        if not ambientes:
            st.info("Nenhum ambiente cadastrado")
        else:
            for a in ambientes:
                col1, col2, col3 = st.columns([6,1,1])

                # Nome
                with col1:
                    st.write(a["nome"])

                # Editar
                with col2:
                    if st.button("✏️", key=f"edit_amb_{a['id']}"):
                        st.session_state["edit_ambiente"] = a

                # Deletar
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
            if st.button("Sim, excluir"):

                try:
                    # deletar itens
                    supabase.table("itens_inventario") \
                        .delete() \
                        .eq("ambiente_id", amb["id"]) \
                        .execute()

                    # deletar ambiente
                    supabase.table("ambientes") \
                        .delete() \
                        .eq("id", amb["id"]) \
                        .execute()

                    st.success("Ambiente excluído!")
                    del st.session_state["confirm_delete_ambiente"]
                    st.rerun()

                except Exception as e:
                    st.error("Erro:")
                    st.write(e)

        with col2:
            if st.button("Cancelar"):
                del st.session_state["confirm_delete_ambiente"]
                st.rerun()

    # -------------------------
    # EDITAR AMBIENTE
    # -------------------------
    if "edit_ambiente" in st.session_state:

        amb = st.session_state["edit_ambiente"]

        st.subheader("✏️ Editar Ambiente")

        novo_nome = st.text_input("Novo nome", value=amb["nome"])

        if st.button("Salvar alteração"):
            supabase.table("ambientes") \
                .update({"nome": novo_nome}) \
                .eq("id", amb["id"]) \
                .execute()

            st.success("Atualizado!")
            del st.session_state["edit_ambiente"]
            st.rerun()

with aba3:
    st.header("📦 Materiais base")

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
    st.header("📋 Itens")

    # =========================
    # CADASTRO DE ITEM
    # =========================
    st.subheader("➕ Cadastrar Item")

    unidades = supabase.table("unidades").select("*").execute().data
    materiais = supabase.table("materiais").select("*").execute().data

    # Selecionar unidade
    unidade_sel = st.selectbox(
        "Unidade",
        unidades,
        format_func=lambda x: x["nome"],
        key="item_unidade"
    )

    # Buscar ambientes da unidade
    ambientes = supabase.table("ambientes") \
        .select("*") \
        .eq("unidade_id", unidade_sel["id"]) \
        .execute().data

    ambiente_sel = st.selectbox(
        "Ambiente",
        ambientes,
        format_func=lambda x: x["nome"],
        key="item_ambiente"
    )

    # Material com opção "Outro"
    lista_materiais = materiais + [{"id": "outro", "nome": "Outro..."}]

    material_sel = st.selectbox(
        "Material",
        lista_materiais,
        format_func=lambda x: x["nome"],
        key="item_material"
    )

    if material_sel["id"] == "outro":
        novo_material = st.text_input("Nome do novo material", key="novo_mat_item")
    else:
        novo_material = None

    patrimonio = st.text_input("Patrimônio", key="patrimonio_item")

    status = st.selectbox("Status", [
        "satisfatorio",
        "trocar_nao_urgente",
        "trocar_urgente"
    ], key="status_item")

    if st.button("Salvar Item", key="btn_salvar_item"):

        # Criar material se for "outro"
        if material_sel["id"] == "outro":
            if not novo_material:
                st.warning("Digite o nome do material")
                st.stop()

            mat = supabase.table("materiais").insert({
                "nome": novo_material
            }).execute().data

            material_id = mat[0]["id"]

        else:
            material_id = material_sel["id"]

        supabase.table("itens_inventario").insert({
            "ambiente_id": ambiente_sel["id"],
            "material_id": material_id,
            "patrimonio": patrimonio,
            "status": status
        }).execute()

        st.success("Item cadastrado!")
        st.rerun()

# =========================
# FILTROS
# =========================
st.subheader("🔎 Consulta de Itens")

col1, col2, col3 = st.columns(3)

with col1:
    f_unidade = st.selectbox(
        "Unidade",
        ["Todas"] + [u["nome"] for u in unidades],
        key="filtro_unidade_tree"
    )

with col2:
    f_material = st.text_input("Material", key="filtro_material_tree")

with col3:
    f_status = st.selectbox(
        "Status",
        ["Todos", "satisfatorio", "trocar_nao_urgente", "trocar_urgente"],
        key="filtro_status_tree"
    )

# =========================
# CARREGAR DADOS
# =========================
ambientes = supabase.table("ambientes").select("*").execute().data
materiais = supabase.table("materiais").select("*").execute().data
itens = supabase.table("itens_inventario").select("*").execute().data

dict_amb = {a["id"]: a for a in ambientes}
dict_mat = {m["id"]: m for m in materiais}
dict_uni = {u["id"]: u for u in unidades}

# =========================
# ORGANIZAR HIERARQUIA
# =========================
estrutura = {}

for item in itens:
    amb = dict_amb.get(item["ambiente_id"], {})
    mat = dict_mat.get(item["material_id"], {})
    uni = dict_uni.get(amb.get("unidade_id"), {})

    # FILTROS
    if f_unidade != "Todas" and uni.get("nome") != f_unidade:
        continue

    if f_material and f_material.lower() not in mat.get("nome", "").lower():
        continue

    if f_status != "Todos" and item["status"] != f_status:
        continue

    unidade_nome = uni.get("nome", "Sem unidade")
    ambiente_nome = amb.get("nome", "Sem ambiente")

    estrutura.setdefault(unidade_nome, {})
    estrutura[unidade_nome].setdefault(ambiente_nome, [])
    estrutura[unidade_nome][ambiente_nome].append({
        "id": item["id"],
        "material": mat.get("nome"),
        "patrimonio": item["patrimonio"],
        "status": item["status"]
    })

# =========================
# CORES
# =========================
def cor(s):
    if s == "trocar_urgente":
        return "🔴"
    elif s == "trocar_nao_urgente":
        return "🟡"
    else:
        return "🟢"

# =========================
# EXIBIÇÃO HIERÁRQUICA
# =========================
if not estrutura:
    st.info("Nenhum item encontrado")
else:
    for unidade, ambientes in estrutura.items():

        with st.expander(f"🏥 {unidade}", expanded=True):

            for ambiente, itens_lista in ambientes.items():

                with st.expander(f"📍 {ambiente}", expanded=False):

                    for i in itens_lista:
                        col1, col2, col3 = st.columns([6,1,1])
                    
                        with col1:
                            st.write(
                                cor(i["status"]),
                                i["material"],
                                "| Patrimônio:",
                                i["patrimonio"]
                            )
                    
                        with col2:
                            if st.button("✏️", key=f"edit_item_{i['id']}"):
                                st.session_state["edit_item"] = {
                                    "item": i,
                                    "ambiente": ambiente,
                                    "unidade": unidade
                                }
                    
                        with col3:
                            if st.button("🗑️", key=f"del_item_{i['id']}"):
                                st.session_state["confirm_delete_item"] = {
                                    "item": i,
                                    "ambiente": ambiente,
                                    "unidade": unidade
                                }
                    
                        # 🔥 EDITAR DENTRO DO AMBIENTE
                        if "edit_item" in st.session_state and st.session_state["edit_item"]["item"]["id"] == i["id"]:
                    
                            item = st.session_state["edit_item"]["item"]
                    
                            st.markdown("**✏️ Editando item:**")
                    
                            novo_patrimonio = st.text_input(
                                "Patrimônio",
                                value=item["patrimonio"],
                                key=f"edit_p_{item['id']}"
                            )
                    
                            novo_status = st.selectbox(
                                "Status",
                                ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"],
                                index=["satisfatorio", "trocar_nao_urgente", "trocar_urgente"].index(item["status"]),
                                key=f"edit_s_{item['id']}"
                            )
                    
                            col_a, col_b = st.columns(2)
                    
                            with col_a:
                                if st.button("Salvar", key=f"save_{item['id']}"):
                                    supabase.table("itens_inventario") \
                                        .update({
                                            "patrimonio": novo_patrimonio,
                                            "status": novo_status
                                        }) \
                                        .eq("id", item["id"]) \
                                        .execute()
                    
                                    st.success("Atualizado!")
                                    del st.session_state["edit_item"]
                                    st.rerun()
                    
                            with col_b:
                                if st.button("Cancelar", key=f"cancel_{item['id']}"):
                                    del st.session_state["edit_item"]
                                    st.rerun()
                    
                        # 🔥 DELETE DENTRO DO AMBIENTE
                        if "confirm_delete_item" in st.session_state and st.session_state["confirm_delete_item"]["item"]["id"] == i["id"]:
                    
                            item = st.session_state["confirm_delete_item"]["item"]
                    
                            st.warning("Excluir este item?")
                    
                            col_a, col_b = st.columns(2)
                    
                            with col_a:
                                if st.button("Sim", key=f"del_yes_{item['id']}"):
                    
                                    supabase.table("itens_inventario") \
                                        .delete() \
                                        .eq("id", item["id"]) \
                                        .execute()
                    
                                    st.success("Excluído!")
                                    del st.session_state["confirm_delete_item"]
                                    st.rerun()
                    
                            with col_b:
                                if st.button("Não", key=f"del_no_{item['id']}"):
                                    del st.session_state["confirm_delete_item"]
                                    st.rerun()
                    
                    if "confirm_delete_item" in st.session_state:
                    
                        item = st.session_state["confirm_delete_item"]
                    
                        st.warning("Deseja excluir este item?")
                    
                        col1, col2 = st.columns(2)
                    
                        with col1:
                            if st.button("Sim, excluir", key="conf_del_item"):
                    
                                supabase.table("itens_inventario") \
                                    .delete() \
                                    .eq("id", item["id"]) \
                                    .execute()
                    
                                st.success("Item excluído!")
                                del st.session_state["confirm_delete_item"]
                                st.rerun()
                    
                        with col2:
                            if st.button("Cancelar", key="cancel_del_item"):
                                del st.session_state["confirm_delete_item"]
                                st.rerun()


if "edit_item" in st.session_state:

    item = st.session_state["edit_item"]

    st.subheader("✏️ Editar Item")

    novo_patrimonio = st.text_input(
        "Patrimônio",
        value=item["patrimonio"],
        key="edit_patrimonio"
    )

    novo_status = st.selectbox(
        "Status",
        ["satisfatorio", "trocar_nao_urgente", "trocar_urgente"],
        index=["satisfatorio", "trocar_nao_urgente", "trocar_urgente"].index(item["status"]),
        key="edit_status"
    )

    if st.button("Salvar alteração", key="salvar_item"):

        supabase.table("itens_inventario") \
            .update({
                "patrimonio": novo_patrimonio,
                "status": novo_status
            }) \
            .eq("id", item["id"]) \
            .execute()

        st.success("Item atualizado!")
        del st.session_state["edit_item"]
        st.rerun()
