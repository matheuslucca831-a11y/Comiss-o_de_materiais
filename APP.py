from supabase import create_client

url = "https://oudfbraxmwuskdnnlisf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im91ZGZicmF4bXd1c2tkbm5saXNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4Nzc5NzQsImV4cCI6MjA4OTQ1Mzk3NH0.QnL67maBxqsfgm4xHmLBYcqPbQ99swjHw3OzndSM9qA"

supabase = create_client(url, key)

import streamlit as st

st.set_page_config(page_title="Controle de Materiais", layout="wide")

st.title("Sistema de Controle de Materiais")

st.write("Use o menu lateral para navegar.")

import streamlit as st

st.title("Cadastro")


st.write("TESTE CONEXÃO")

teste = supabase.table("ambientes").select("*").execute()

st.write(teste)

# =========================
# CADASTRAR AMBIENTE
# =========================
st.subheader("Novo Ambiente")

nome = st.text_input("Nome do ambiente")
unidade = st.text_input("Unidade")

if st.button("Salvar Ambiente"):
    supabase.table("ambientes").insert({
        "nome": nome,
        "unidade": unidade
    }).execute()
    st.success("Ambiente criado!")

# =========================
# CADASTRAR ITEM
# =========================
st.subheader("Cadastrar Item")

ambientes = supabase.table("ambientes").select("*").execute().data
materiais = supabase.table("materiais").select("*").execute().data

ambiente = st.selectbox("Ambiente", [a["nome"] for a in ambientes])

lista_materiais = [m["nome"] for m in materiais] + ["Outro..."]
material_sel = st.selectbox("Material", lista_materiais)

if material_sel == "Outro...":
    material_nome = st.text_input("Novo material")
else:
    material_nome = material_sel

patrimonio = st.text_input("Patrimônio")

status = st.selectbox("Status", [
    "satisfatorio",
    "trocar_nao_urgente",
    "trocar_urgente"
])

if st.button("Salvar Item"):

    mat = supabase.table("materiais").select("*").eq("nome", material_nome).execute().data

    if not mat:
        mat = supabase.table("materiais").insert({
            "nome": material_nome
        }).execute().data

    material_id = mat[0]["id"]
    ambiente_id = [a["id"] for a in ambientes if a["nome"] == ambiente][0]

    item = supabase.table("itens_inventario").insert({
        "ambiente_id": ambiente_id,
        "material_id": material_id,
        "patrimonio": patrimonio,
        "status": status
    }).execute().data

    # HISTÓRICO
    supabase.table("movimentacoes").insert({
        "item_id": item[0]["id"],
        "ambiente_id": ambiente_id,
        "material_id": material_id,
        "tipo": "entrada",
        "usuario": "admin"
    }).execute()

    st.success("Item cadastrado!")


import streamlit as st

st.title("Consulta")

busca = st.text_input("Buscar material ou patrimônio")

filtro_status = st.selectbox("Status", [
    "Todos",
    "satisfatorio",
    "trocar_nao_urgente",
    "trocar_urgente"
])

dados = supabase.table("itens_inventario") \
    .select("id, patrimonio, status, ambientes(nome, unidade), materiais(nome)") \
    .execute().data

resultado = []

for item in dados:
    if (
        busca.lower() in str(item["patrimonio"]).lower()
        or busca.lower() in item["materiais"]["nome"].lower()
    ):
        if filtro_status == "Todos" or item["status"] == filtro_status:
            resultado.append(item)

def status_icon(s):
    if s == "trocar_urgente":
        return "🔴"
    elif s == "trocar_nao_urgente":
        return "🟡"
    else:
        return "🟢"

for r in resultado:
    st.write(
        status_icon(r["status"]),
        r["ambientes"]["unidade"],
        r["ambientes"]["nome"],
        r["materiais"]["nome"],
        r["patrimonio"]
    )


import streamlit as st

st.title("Movimentações")

dados = supabase.table("itens_inventario") \
    .select("id, patrimonio, status, materiais(nome)") \
    .execute().data

item_sel = st.selectbox(
    "Selecionar item",
    dados,
    format_func=lambda x: f'{x["materiais"]["nome"]} - {x["patrimonio"]}'
)

novo_status = st.selectbox("Novo status", [
    "satisfatorio",
    "trocar_nao_urgente",
    "trocar_urgente"
])

if st.button("Atualizar"):

    supabase.table("itens_inventario") \
        .update({"status": novo_status}) \
        .eq("id", item_sel["id"]) \
        .execute()

    supabase.table("movimentacoes").insert({
        "item_id": item_sel["id"],
        "material_id": item_sel["materiais"]["nome"],
        "tipo": "troca_status",
        "usuario": "admin"
    }).execute()

    st.success("Status atualizado!")
