# 📊 MTSistem – Sistema Fiscal

Sistema desktop desenvolvido em **Python**, voltado para controle fiscal interno, com foco em **organização, validação e confiabilidade de dados**, além de um **mecanismo próprio de controle de versões e atualizações**.

---

## 🚀 Visão Geral

O **MTSistem – Sistema Fiscal** é uma aplicação desktop para ambiente Windows, desenvolvida com interface moderna baseada em **Tkinter + ttk**, projetada para uso empresarial e administrativo.

O sistema possui:
- Controle de usuários e permissões
- Tela administrativa de configurações
- Controle centralizado de versões
- Sistema de atualização gerenciado via banco de dados
- Estrutura preparada para empacotamento em executável (.exe)

---

## 🧩 Funcionalidades Implementadas

### 🔐 Autenticação e Controle de Acesso
- Login por usuário com senha criptografada
- Diferenciação entre **usuário comum** e **administrador**
- Bloqueio global do sistema via configuração no banco de dados
  - Quando ativo, **somente administradores conseguem acessar**
- Autenticação centralizada via DAO

---

### ⚙️ Configurações do Sistema (Admin)
Tela exclusiva para administradores com controle direto via banco de dados.

Configurações armazenadas na tabela `configuracoes`:
- `versao_atual` – versão oficial do sistema
- `atualizacao_liberada` – libera ou bloqueia atualização para usuários comuns
- `sistema_bloqueado` – bloqueia acesso geral (exceto admin)
- `mensagem_update` – mensagem exibida na tela inicial quando o sistema está desatualizado
- `exe_atualizacao` – caminho ou nome do executável de atualização

Todas as configurações podem ser alteradas **em tempo real** pela interface administrativa.

---

### 🔄 Controle de Versão e Atualização
- Comparação automática entre:
  - Versão local do sistema
  - Versão registrada no banco de dados
- Detecção de sistema desatualizado
- Exibição de aviso na tela inicial (Home)
- Mensagem de atualização configurável via banco
- Botão de atualização:
  - Ativado ou desativado conforme configuração
  - Liberação especial para administradores

---

### 🏠 Tela Inicial (Home)
- Mensagem de boas-vindas personalizada
- Exibição condicional de aviso de sistema desatualizado
- Mensagem dinâmica vinda do banco de dados
- Interface responsiva e consistente com o tema do sistema

---

### 🎨 Interface Gráfica
- Layout moderno com:
  - Menu lateral
  - Cards
  - Ícones personalizados
- Estilização centralizada via `ttk.Style`
- Checkbuttons personalizados mantendo o checkbox nativo
- Ícones carregados com `resource_path`, compatível com executável (.exe)

---

### 🔁 Atualização Dinâmica da Interface
- Estrutura preparada para recarregar telas após alterações administrativas
- Evita reinício completo do sistema para mudanças simples
- Separação clara entre estado visual e estado de dados

---

## 🛠️ Tecnologias Utilizadas

### Linguagem
- **Python 3.12**

### Interface Gráfica
- `tkinter`
- `ttk`
- `Pillow (PIL)`

### Banco de Dados
- **SQLite**
- Padrão DAO
- Tabelas principais:
  - `usuarios`
  - `configuracoes`

### Segurança
- Hash de senhas
- Controle de permissões por nível de usuário

### Empacotamento
- Estrutura preparada para **PyInstaller**
- Uso de `resource_path` para assets
- Execução como aplicativo desktop profissional

---

## 📌 Status do Projeto
✔ Arquitetura organizada  
✔ Controle de versão funcional  
✔ Interface consistente  
✔ Pronto para evolução modular  

---

## 🔮 Próximos Passos
- Melhorar recarregamento dinâmico sem reinício
- Centralizar cache de configurações
- Log de alterações administrativas
- Expansão de módulos fiscais
- Melhorias contínuas de UX/UI

---

## 👨‍💻 Autor
**Miquéias Teles**  
Desenvolvedor do MTSistem  
Sistema desenvolvido para uso real em ambiente empresarial
