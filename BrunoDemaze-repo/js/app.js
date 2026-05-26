// ABRIR PERFIL
function abrirPerfil(nome, idade, profissao, foto, avaliacao){

document.getElementById("perfil").style.display="flex"

document.getElementById("nome").innerText=nome+" - "+idade+" anos"
document.getElementById("profissao").innerText=profissao
document.getElementById("avaliacao").innerText="⭐ "+avaliacao
document.getElementById("foto").src=foto

// SALVAR TEMPORÁRIO PARA CONTRATAR
window.profSelecionado = {
nome, idade, profissao, foto, avaliacao
}
}

// FECHAR PERFIL
function fecharPerfil(){
document.getElementById("perfil").style.display="none"
}

// CONTRATAR
function contratar(){

let lista = JSON.parse(localStorage.getItem("contratados")) || []

lista.push(window.profSelecionado)

localStorage.setItem("contratados", JSON.stringify(lista))

alert("Profissional contratado com sucesso!")

fecharPerfil()
}

// FILTRO POR SERVIÇO
function filtrar(){

let params = new URLSearchParams(window.location.search)
let servico = params.get("servico")

if(!servico) return

let cards = document.querySelectorAll(".prof-card")

cards.forEach(card => {

let texto = card.innerText.toLowerCase()

if(!texto.includes(servico.toLowerCase())){
card.style.display = "none"
}

})
}

filtrar()