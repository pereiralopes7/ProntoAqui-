// ============================================
// AUTENTICAÇÃO - Gerenciamento de Login/Logout
// ============================================

const API_BASE = window.location.origin

// Verificar se usuário está autenticado
function verificarAutenticacao() {
  const token = localStorage.getItem('token')
  const usuario = localStorage.getItem('usuario')
  
  if (!token || !usuario) {
    return false
  }
  return true
}

// Redirecionar para login se não autenticado
function protegerPagina() {
  if (!verificarAutenticacao()) {
    window.location.href = 'login.html'
  }
}

// Fazer login
async function fazerLogin(email, senha) {
  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, senha })
    })

    if (!response.ok) {
      throw new Error('Credenciais inválidas')
    }

    const data = await response.json()
    
    if (data.token) {
      // Guardar token e email do usuário
      localStorage.setItem('token', data.token)
      localStorage.setItem('usuario', email)
      localStorage.setItem('tipo_usuario', data.tipo || 'cliente')
      localStorage.setItem('nome_usuario', data.nome || email)
      
      alert('Login realizado com sucesso!')

// 🔥 REDIRECIONAMENTO POR TIPO
      if (data.tipo === "admin") {
        window.location.href = "admin.html"
      } else {
        window.location.href = "index.html"
      }
      
      return true
    }

    return false
  } catch (error) {
    console.error('Erro ao fazer login:', error)
    alert('Erro: ' + error.message)
    return false
  }
}

// Fazer logout
function fazerLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('usuario')
  localStorage.removeItem('tipo_usuario')
  window.location.href = 'login.html'
}

// Cadastrar novo usuário
async function cadastrarUsuario(nome, email, senha, tipo, descricao = '') {
  try {
    const tipoFinal = tipo === 'profissional' ? 'contratado' : tipo
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        nome,
        email,
        senha,
        tipo: tipoFinal,
        descricao
      })
    })

    if (!response.ok) {
      throw new Error('Erro ao cadastrar usuário')
    }

    alert('Usuário cadastrado com sucesso! Faça login agora.')
    window.location.href = 'login.html'
    return true
  } catch (error) {
    console.error('Erro ao cadastrar:', error)
    alert('Erro: ' + error.message)
    return false
  }
}

// Obter informações do usuário logado
function obterUsuarioLogado() {
  return {
    email: localStorage.getItem('usuario'),
    tipo: localStorage.getItem('tipo_usuario'),
    token: localStorage.getItem('token'),
    nome: localStorage.getItem('nome_usuario')
  }
}

// Mostrar nome do usuário no navbar
function exibirNomeUsuario() {
  const usuario = obterUsuarioLogado()
  const elemento = document.getElementById('usuario-logado')
  
  if (elemento) {
    if (usuario.nome) {
      elemento.innerText = usuario.nome
    } else if (usuario.email) {
      elemento.innerText = usuario.email.split('@')[0]
    }
  }
}
