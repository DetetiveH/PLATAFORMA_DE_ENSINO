Plataforma de Ensino Online - LEGIONARIO.PY
📝 Descrição
Este é um sistema completo de plataforma de ensino online desenvolvido em Python, que permite:

Cadastro e autenticação de usuários (alunos e professores)

Gerenciamento de cursos, lições e avaliações

Acompanhamento de progresso dos alunos

Sistema de mensagens e avisos

Backup e recuperação de dados

Conformidade com LGPD (Lei Geral de Proteção de Dados)

🛠️ Funcionalidades Principais
👨‍🎓 Para Alunos:
Matrícula em cursos disponíveis

Acesso ao conteúdo das aulas

Realização de avaliações

Acompanhamento do progresso

Visualização de mensagens e avisos

👨‍🏫 Para Professores:
Criação e gerenciamento de cursos

Adição/edição de lições e avaliações

Postagem de avisos nos cursos

Envio de mensagens para alunos

Monitoramento do progresso dos alunos

🔧 Administrativas:
Sistema de backup automático

Restauração de backups

Logs detalhados de todas as ações

Gerenciamento de privacidade (LGPD)

⚙️ Tecnologias e Bibliotecas Utilizadas
Python 3.x

Bibliotecas padrão:

json - Para armazenamento e manipulação de dados

os - Para operações do sistema de arquivos

datetime - Para manipulação de datas e horários

hashlib - Para criptografia de senhas (MD5)

logging - Para registro de logs do sistema

re - Para validação de expressões regulares

shutil e zipfile - Para sistema de backup

sys - Para controle do sistema

pathlib - Para manipulação de caminhos de arquivos

📂 Estrutura de Arquivos
LEGIONARIO.PY - Arquivo principal do sistema

dados_plataforma.json - Banco de dados em formato JSON

plataforma_ensino.log - Arquivo de logs do sistema

backups/ - Diretório para armazenamento de backups

🔒 Segurança e Privacidade (LGPD)
O sistema inclui diversos recursos para conformidade com a LGPD:

Criptografia de senhas (MD5)

Anonimização de dados ao excluir contas

Registro detalhado de todas as ações sensíveis

Política de privacidade clara durante o cadastro

Controle de acesso aos dados pessoais

Possibilidade de edição e exclusão de dados

🚀 Como Executar
Certifique-se de ter Python 3.x instalado

Execute o arquivo principal:

bash
python LEGIONARIO.PY
Use as credenciais padrão para teste:

Aluno: usuário "aluno", senha "123456"

Professor: usuário "prof", senha "123456"

🔄 Sistema de Backup
O sistema possui um robusto mecanismo de backup que:

Cria backups automáticos antes de operações críticas

Armazena até 5 backups (rotação automática)

Permite restauração manual de backups anteriores

Compacta os dados em formato ZIP para economia de espaço

📊 Estrutura de Dados
O sistema armazena informações em um formato JSON estruturado:

usuarios: Dados de alunos e professores

cursos: Informações sobre cursos, lições e avaliações

logs_privacidade: Registro de ações sensíveis

termos_uso: Versão atual dos termos de uso

📋 Menu Principal
Fazer login - Acessar como aluno ou professor

Cadastrar novo usuário - Registrar novo aluno ou professor

Visualizar cursos disponíveis - Listar todos os cursos

Backup do sistema - Gerenciar cópias de segurança

Sobre o sistema - Informações sobre a plataforma

Sair - Encerrar o programa

📈 Melhorias Futuras
Implementar criptografia mais segura (bcrypt)

Adicionar sistema de recuperação de senha

Implementar interface gráfica (Tkinter/PyQt)

Adicionar suporte a upload de arquivos (vídeos, PDFs)

Implementar sistema de certificados

Adicionar relatórios estatísticos avançados

⚠️ Limitações Atuais
Armazenamento em arquivo JSON (não escalável para muitos usuários)

Criptografia MD5 (considerada fraca para produção)

Interface apenas em modo texto

Ausência de testes automatizados

📜 Licença
Este projeto é destinado para fins educacionais. O código pode ser livremente utilizado e modificado, desde que mantidos os créditos ao autor original.

