

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

        # Deletar
        with col3:
            if st.button("🗑️", key=f"del_{u['id']}"):
                supabase.table("unidades").delete().eq("id", u["id"]).execute()
                st.success("Unidade excluída!")
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

    unidades = supabase.table("unidades").select("*").execute().data

    if not unidades:
        st.warning("Cadastre uma unidade primeiro")
    else:
        unidade_sel = st.selectbox(
            "Selecione a unidade",
            unidades,
            format_func=lambda x: x["nome"]
        )

        nome_ambiente = st.text_input("Nome do ambiente")

        if st.button("Criar Ambiente"):

            if not nome_ambiente:
                st.warning("Digite o nome do ambiente")

            else:
                try:
                    supabase.table("ambientes").insert({
                        "nome": nome_ambiente,
                        "unidade_id": unidade_sel["id"]
                    }).execute()

                    st.success("Ambiente criado!")

                except Exception as e:
                    st.error("ERRO REAL:")
                    st.write(e)

    ambientes = supabase.table("ambientes").select("*").execute().data

    for a in ambientes:
        st.write(a["nome"])


with aba3:
    st.header("📦 Materiais")

    materiais = supabase.table("materiais").select("*").execute().data

    for m in materiais:
        col1, col2 = st.columns([5,1])

        with col1:
            st.write(m["nome"])

        with col2:
            if st.button("🗑️", key=m["id"]):
                supabase.table("materiais").delete().eq("id", m["id"]).execute()
                st.rerun()

    novo_material = st.text_input("Novo material")

    if st.button("Adicionar"):
        supabase.table("materiais").insert({
            "nome": novo_material
        }).execute()
        st.success("Material criado!")


with aba4:
    st.header("📋 Cadastro de Item")

    ambientes = supabase.table("ambientes").select("*").execute().data
    materiais = supabase.table("materiais").select("*").execute().data

    ambiente_sel = st.selectbox(
        "Ambiente",
        ambientes,
        format_func=lambda x: x["nome"]
    )

    material_sel = st.selectbox(
        "Material",
        materiais,
        format_func=lambda x: x["nome"]
    )

    patrimonio = st.text_input("Patrimônio")

    status = st.selectbox("Status", [
        "satisfatorio",
        "trocar_nao_urgente",
        "trocar_urgente"
    ])

    if st.button("Salvar Item"):
        supabase.table("itens_inventario").insert({
            "ambiente_id": ambiente_sel["id"],
            "material_id": material_sel["id"],
            "patrimonio": patrimonio,
            "status": status
        }).execute()

        st.success("Item cadastrado!")
