// ============================================
// API - Chamadas centralizadas para o backend
// ============================================

const API_BASE = window.location.origin

// Função auxiliar para fazer requisições com token
async function fazerRequisicao(endpoint, metodo = 'GET', dados = null) {
  const token = localStorage.getItem('token')
  
  const headers = {
    'Content-Type': 'application/json'
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const config = {
    method: metodo,
    headers
  }
  
  if (dados) {
    config.body = JSON.stringify(dados)
  }
  
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config)
    
    if (response.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('token')
      window.location.href = 'login.html'
      return null
    }
    
    return await response.json()
  } catch (error) {
    console.error('Erro na requisição:', error)
    return null
  }
}

// ============================================
// SERVIÇOS / ATIVIDADES
// ============================================

// Obter todos os serviços
async function obterServicos() {
  return await fazerRequisicao('/servicos')
}

// Criar novo serviço/atividade
async function criarServico(titulo, descricao, categoria, preco) {
  const usuario = obterUsuarioLogado()
  
  return await fazerRequisicao('/servicos', 'POST', {
    titulo,
    descricao,
    categoria,
    preco,
    profissional_id: usuario.email
  })
}

// Atualizar serviço
async function atualizarServico(servico_id, dados) {
  return await fazerRequisicao(`/servicos/${servico_id}`, 'PUT', dados)
}

// Deletar serviço
async function deletarServico(servico_id) {
  return await fazerRequisicao(`/servicos/${servico_id}`, 'DELETE')
}

// ============================================
// USUÁRIOS
// ============================================

// Obter profissionais
async function obterProfissionais(filtro = '') {
  return await fazerRequisicao(`/profissionais?filtro=${filtro}`)
}

// Obter dados do usuário
async function obterPerfilUsuario(email) {
  return await fazerRequisicao(`/usuarios/${email}`)
}

// ============================================
// CONTRATOS / PAGAMENTOS
// ============================================

// Criar contrato
async function criarContrato(servico_id, cliente_id) {
  return await fazerRequisicao('/contratos', 'POST', {
    servico_id,
    cliente_id
  })
}

// Registrar pagamento
async function registrarPagamento(contrato_id, valor, metodo) {
  const usuario = obterUsuarioLogado()
  return await fazerRequisicao('/pagar', 'POST', {
    servico_id: contrato_id,
    pagador_id: usuario?.id,
    recebedor_id: null,
    valor,
    metodo
  })
}

// ============================================
// CHAT
// ============================================

// Obter mensagens de uma conversa
async function obterMensagens(conversa_id) {
  return await fazerRequisicao(`/chat/${conversa_id}`)
}

// Enviar mensagem
async function enviarMensagem(conversa_id, mensagem) {
  return await fazerRequisicao(`/chat/${conversa_id}`, 'POST', {
    mensagem
  })
}
