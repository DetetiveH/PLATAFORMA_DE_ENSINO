import json
import os
from datetime import datetime
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import re
import shutil
import zipfile
import sys
from pathlib import Path

# Configuração de logs
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('plataforma_ensino.log', maxBytes=5*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Estrutura de dados inicial
dados_iniciais = {
    "usuarios": {
        "aluno": {
            "senha": "e10adc3949ba59abbe56e057f20f883e",  # "123456" em MD5
            "tipo": "aluno",
            "cursos_matriculados": [],
            "progresso": {},
            "mensagens": {},
            "dados_pessoais": {
                "nome": "Aluno Teste",
                "email": "aluno@teste.com",
                "data_nascimento": "01/01/2000",
                "cpf": "000.000.000-00"
            },
            "termos_aceitos": True,
            "data_cadastro": "01/01/2023",
            "ultimo_acesso": "01/01/2023"
        },
        "prof": {
            "senha": "e10adc3949ba59abbe56e057f20f883e",  # "123456" em MD5
            "tipo": "professor",
            "cursos_criados": [],
            "mensagens": {},
            "dados_pessoais": {
                "nome": "Professor Teste",
                "email": "prof@teste.com",
                "data_nascimento": "01/01/1980",
                "cpf": "111.111.111-11"
            },
            "termos_aceitos": True,
            "data_cadastro": "01/01/2023",
            "ultimo_acesso": "01/01/2023"
        }
    },
    "cursos": {
        "iniciante": {
            "Introdução ao Python": {
                "descricao": "Curso básico de Python para iniciantes",
                "dificuldade": "Fácil",
                "professor": "prof",
                "licoes": {
                    "1. Introdução": {
                        "conteudo": "Bem-vindo ao curso de Python! Nesta lição você aprenderá os conceitos básicos.",
                        "concluida": False
                    },
                    "2. Primeiros Passos": {
                        "conteudo": "Aqui você vai escrever seu primeiro programa em Python.",
                        "concluida": False
                    }
                },
                "avaliacoes": [
                    {
                        "titulo": "Quiz Inicial",
                        "perguntas": [
                            {
                                "pergunta": "O que é Python?",
                                "opcoes": ["Linguagem de programação", "Tipo de cobra", "Editor de texto"],
                                "resposta": 0
                            }
                        ]
                    }
                ],
                "avisos": []
            }
        }
    },
    "logs_privacidade": [],
    "termos_uso": {
        "versao": "1.0",
        "data_implementacao": "01/01/2023",
        "conteudo": "Termos de uso da plataforma..."
    }
}

class BackupManager:
    BACKUP_DIR = "backups"
    MAX_BACKUPS = 5  # Número máximo de backups a manter
    
    @classmethod
    def criar_backup(cls):
        try:
            # Criar diretório de backups se não existir
            os.makedirs(cls.BACKUP_DIR, exist_ok=True)
            
            # Nome do arquivo de backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"plataforma_backup_{timestamp}.zip"
            backup_path = os.path.join(cls.BACKUP_DIR, backup_name)
            
            # Arquivos a serem incluídos no backup
            files_to_backup = [
                'dados_plataforma.json',
                'plataforma_ensino.log'
            ]
            
            # Criar arquivo ZIP com os arquivos
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files_to_backup:
                    if os.path.exists(file):
                        zipf.write(file)
            
            logger.info(f"Backup criado com sucesso: {backup_path}")
            
            # Limitar número de backups
            cls._limitar_backups()
            
            return True
        except Exception as e:
            logger.error(f"Falha ao criar backup: {str(e)}")
            return False
    
    @classmethod
    def _limitar_backups(cls):
        try:
            if not os.path.exists(cls.BACKUP_DIR):
                return
            
            # Listar todos os backups ordenados por data (mais antigo primeiro)
            backups = []
            for file in os.listdir(cls.BACKUP_DIR):
                if file.startswith("plataforma_backup_") and file.endswith(".zip"):
                    file_path = os.path.join(cls.BACKUP_DIR, file)
                    backups.append((file_path, os.path.getmtime(file_path)))
            
            # Ordenar por data de modificação (mais antigo primeiro)
            backups.sort(key=lambda x: x[1])
            
            # Remover backups excedentes
            while len(backups) > cls.MAX_BACKUPS:
                oldest_backup = backups.pop(0)
                try:
                    os.remove(oldest_backup[0])
                    logger.info(f"Backup antigo removido: {oldest_backup[0]}")
                except Exception as e:
                    logger.error(f"Falha ao remover backup antigo {oldest_backup[0]}: {str(e)}")
        except Exception as e:
            logger.error(f"Falha ao limitar backups: {str(e)}")
    
    @classmethod
    def restaurar_backup(cls, backup_path=None):
        try:
            if not backup_path:
                # Se nenhum backup for especificado, usar o mais recente
                if not os.path.exists(cls.BACKUP_DIR):
                    logger.error("Nenhum backup disponível para restaurar")
                    return False
                
                backups = []
                for file in os.listdir(cls.BACKUP_DIR):
                    if file.startswith("plataforma_backup_") and file.endswith(".zip"):
                        file_path = os.path.join(cls.BACKUP_DIR, file)
                        backups.append((file_path, os.path.getmtime(file_path)))
                
                if not backups:
                    logger.error("Nenhum backup disponível para restaurar")
                    return False
                
                # Ordenar por data (mais recente primeiro)
                backups.sort(key=lambda x: x[1], reverse=True)
                backup_path = backups[0][0]
            
            # Criar backup atual antes de restaurar
            cls.criar_backup()
            
            # Extrair arquivos do backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall()
            
            logger.info(f"Backup restaurado com sucesso: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Falha ao restaurar backup: {str(e)}")
            return False
    
    @classmethod
    def listar_backups(cls):
        try:
            if not os.path.exists(cls.BACKUP_DIR):
                return []
            
            backups = []
            for file in os.listdir(cls.BACKUP_DIR):
                if file.startswith("plataforma_backup_") and file.endswith(".zip"):
                    file_path = os.path.join(cls.BACKUP_DIR, file)
                    backups.append({
                        'nome': file,
                        'caminho': file_path,
                        'data': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d/%m/%Y %H:%M:%S"),
                        'tamanho': f"{os.path.getsize(file_path) / 1024:.2f} KB"
                    })
            
            # Ordenar por data (mais recente primeiro)
            backups.sort(key=lambda x: os.path.getmtime(x['caminho']), reverse=True)
            return backups
        except Exception as e:
            logger.error(f"Falha ao listar backups: {str(e)}")
            return []

class PlataformaEnsino:
    def __init__(self):
        self.dados = dados_iniciais
        self.usuario_atual = None
        self.carregar_dados()
    
    # Funções de persistência de dados
    def salvar_dados(self):
        try:
            # Criar backup antes de salvar
            BackupManager.criar_backup()
            
            with open('dados_plataforma.json', 'w') as arquivo:
                json.dump(self.dados, arquivo, indent=4, ensure_ascii=False)
            logger.info("Dados salvos com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")
            raise Exception("Erro ao salvar dados. Por favor, tente novamente.")
    
    def carregar_dados(self):
        try:
            if os.path.exists('dados_plataforma.json'):
                with open('dados_plataforma.json', 'r') as arquivo:
                    self.dados = json.load(arquivo)
                logger.info("Dados carregados com sucesso")
            else:
                self.salvar_dados()
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            print("\nErro ao carregar dados. Tentando restaurar backup...")
            if BackupManager.restaurar_backup():
                print("Backup restaurado com sucesso. Tente novamente.")
            else:
                print("Usando dados iniciais.")
    
    # Funções auxiliares
    def _criptografar_senha(self, senha):
        """Criptografa a senha usando MD5 (apenas para fins didáticos, em produção usar bcrypt ou similar)"""
        return hashlib.md5(senha.encode('utf-8')).hexdigest()
    
    def _validar_email(self, email):
        """Valida o formato do email"""
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None
    
    def _validar_cpf(self, cpf):
        """Valida o formato do CPF (apenas formato, não valida dígitos verificadores)"""
        regex = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
        return re.match(regex, cpf) is not None
    
    def _validar_data(self, data):
        """Valida o formato da data (DD/MM/AAAA)"""
        try:
            datetime.strptime(data, '%d/%m/%Y')
            return True
        except ValueError:
            return False
    
    def _registrar_log_privacidade(self, acao, detalhes):
        """Registra logs de privacidade para conformidade com LGPD"""
        log = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario": self.usuario_atual if self.usuario_atual else "Sistema",
            "acao": acao,
            "detalhes": detalhes
        }
        self.dados["logs_privacidade"].append(log)
        logger.info(f"Log de privacidade: {acao} - {detalhes}")
    
    def _validar_entrada(self, valor, tipo, obrigatorio=True, min_len=None, max_len=None, opcoes=None):
        """Valida entradas do usuário de forma genérica"""
        if obrigatorio and not valor:
            raise ValueError("Este campo é obrigatório.")
        
        if valor:
            if min_len is not None and len(valor) < min_len:
                raise ValueError(f"O campo deve ter no mínimo {min_len} caracteres.")
            
            if max_len is not None and len(valor) > max_len:
                raise ValueError(f"O campo deve ter no máximo {max_len} caracteres.")
            
            if tipo == "email" and not self._validar_email(valor):
                raise ValueError("Email inválido.")
            
            if tipo == "cpf" and not self._validar_cpf(valor):
                raise ValueError("CPF inválido. Formato esperado: 000.000.000-00")
            
            if tipo == "data" and not self._validar_data(valor):
                raise ValueError("Data inválida. Formato esperado: DD/MM/AAAA")
            
            if tipo == "numero":
                if not valor.isdigit():
                    raise ValueError("Este campo deve conter apenas números.")
            
            if opcoes is not None and valor not in opcoes:
                raise ValueError(f"Opção inválida. As opções válidas são: {', '.join(opcoes)}")
        
        return valor
    
    # Funções de autenticação
    def cadastrar_usuario(self):
        try:
            print("\n--- CADASTRO DE USUÁRIO ---")
            
            # Aceitar termos de uso
            print("\nTERMOS DE USO E POLÍTICA DE PRIVACIDADE")
            print("\n========== TERMOS DE USO E POLÍTICA DE PRIVACIDADE ==========\n")

            print("Este sistema educacional tem como finalidade promover a inclusão digital, oferecendo cursos e conteúdos voltados")
            print("para o desenvolvimento de competências técnicas e digitais. Para utilizar esta plataforma, será necessário realizar")
            print("um cadastro com seus dados pessoais, os quais serão tratados de forma ética, segura e em conformidade com a")
            print("Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD).\n")

            print("➡️ DADOS COLETADOS:")
            print("- Nome completo")
            print("- Endereço de e-mail")
            print("- CPF")
            print("- Data de nascimento")
            print("- Senha (armazenada de forma criptografada)\n")

            print("➡️ FINALIDADE DO USO DOS DADOS:")
            print("- Identificação e autenticação segura do usuário")
            print("- Atribuição de perfil (aluno ou professor)")
            print("- Acompanhamento de progresso e desempenho educacional")
            print("- Emissão de relatórios e controle de acesso")
            print("- Registro de atividades para fins de segurança e auditoria\n")

            print("➡️ TRATAMENTO E PROTEÇÃO DOS DADOS:")
            print("- Suas informações são armazenadas localmente em arquivos protegidos.")
            print("- A senha é armazenada de forma criptografada (hash seguro).")
            print("- As ações sensíveis (cadastro, login, exclusão, etc.) são registradas em arquivos de log.")
            print("- Seus dados não serão compartilhados com terceiros em nenhuma hipótese.")
            print("- Você poderá solicitar, a qualquer momento, a exclusão ou anonimização dos seus dados.\n")

            print("➡️ DIREITOS DO TITULAR (VOCÊ):")
            print("- Confirmar a existência de tratamento dos seus dados")
            print("- Acessar, corrigir ou excluir seus dados pessoais")
            print("- Revogar o consentimento dado para uso dos dados")
            print("- Obter informações sobre como seus dados são utilizados\n")

            print("Este Termo de Uso poderá ser atualizado periodicamente. Você será avisado em caso de alterações significativas.\n")

            print("🔒 Ao prosseguir, você declara que leu, compreendeu e está de acordo com os Termos de Uso e a Política de Privacidade.\n")

            print(self.dados["termos_uso"]["conteudo"])
            aceitar = input("\nVocê aceita os termos de uso e política de privacidade? (s/n): ").lower()
            
            if aceitar != 's':
                print("\nÉ necessário aceitar os termos para se cadastrar.")
                return
            
            # Coletar dados do usuário
            tipo = input("\nVocê é aluno ou professor? (a/p): ").lower()
            self._validar_entrada(tipo, "opcao", opcoes=['a', 'p'])
            
            usuario = input("\nDigite um nome de usuário (3-20 caracteres): ")
            self._validar_entrada(usuario, "texto", min_len=3, max_len=20)
            
            if usuario in self.dados['usuarios']:
                raise ValueError("Este usuário já existe!")
            
            senha = input("\nDigite uma senha (mínimo 6 caracteres): ")
            self._validar_entrada(senha, "texto", min_len=6)
            
            # Dados pessoais para conformidade com LGPD
            print("\n--- DADOS PESSOAIS ---")
            nome = input("Nome completo: ")
            self._validar_entrada(nome, "texto", min_len=5)
            
            email = input("Email: ")
            self._validar_entrada(email, "email")
            
            data_nascimento = input("Data de nascimento (DD/MM/AAAA): ")
            self._validar_entrada(data_nascimento, "data")
            
            cpf = input("CPF (000.000.000-00): ")
            self._validar_entrada(cpf, "cpf")
            
            tipo_completo = "aluno" if tipo == 'a' else "professor"
            
            # Criar usuário
            self.dados['usuarios'][usuario] = {
                "senha": self._criptografar_senha(senha),
                "tipo": tipo_completo,
                "cursos_matriculados": [],
                "progresso": {},
                "mensagens": {},
                "dados_pessoais": {
                    "nome": nome,
                    "email": email,
                    "data_nascimento": data_nascimento,
                    "cpf": cpf
                },
                "termos_aceitos": True,
                "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                "ultimo_acesso": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            if tipo_completo == "professor":
                self.dados['usuarios'][usuario]['cursos_criados'] = []
            
            self.salvar_dados()
            self._registrar_log_privacidade("Cadastro de usuário", f"Novo {tipo_completo} cadastrado: {usuario}")
            print(f"\nCadastro de {tipo_completo} realizado com sucesso!")
            logger.info(f"Novo usuário cadastrado: {usuario}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro no cadastro: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado durante o cadastro.")
            logger.error(f"Erro inesperado no cadastro: {str(e)}")
    
    def fazer_login(self):
        try:
            print("\n--- LOGIN ---")
            usuario = input("Usuário: ")
            senha = input("Senha: ")
            
            if usuario not in self.dados['usuarios']:
                raise ValueError("Usuário não encontrado!")
            
            senha_criptografada = self._criptografar_senha(senha)
            if self.dados['usuarios'][usuario]['senha'] != senha_criptografada:
                raise ValueError("Senha incorreta!")
            
            # Atualizar último acesso
            self.dados['usuarios'][usuario]['ultimo_acesso'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            self.salvar_dados()
            
            print(f"\nBem-vindo(a), {usuario}!")
            self.usuario_atual = usuario
            self._registrar_log_privacidade("Login", f"Usuário {usuario} fez login")
            logger.info(f"Usuário {usuario} fez login")
            return True
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Falha no login: {str(e)}")
            return False
        except Exception as e:
            print("\nOcorreu um erro inesperado durante o login.")
            logger.error(f"Erro inesperado no login: {str(e)}")
            return False
    
    def sair(self):
        try:
            print("\nSaindo da conta...")
            if self.usuario_atual:
                self._registrar_log_privacidade("Logout", f"Usuário {self.usuario_atual} fez logout")
                logger.info(f"Usuário {self.usuario_atual} fez logout")
            self.salvar_dados()
            self.usuario_atual = None
        except Exception as e:
            print("\nOcorreu um erro ao sair da conta.")
            logger.error(f"Erro ao sair: {str(e)}")
    
    # Funções de privacidade (LGPD)
    def visualizar_dados_pessoais(self):
        try:
            if not self.usuario_atual:
                raise ValueError("Nenhum usuário logado.")
            
            dados = self.dados['usuarios'][self.usuario_atual]['dados_pessoais']
            
            print("\n--- SEUS DADOS PESSOAIS ---")
            print(f"Nome: {dados['nome']}")
            print(f"Email: {dados['email']}")
            print(f"Data de Nascimento: {dados['data_nascimento']}")
            print(f"CPF: {dados['cpf']}")
            
            self._registrar_log_privacidade("Visualização de dados", f"Usuário {self.usuario_atual} visualizou dados pessoais")
            input("\nPressione Enter para voltar...")
        
        except Exception as e:
            print(f"\nErro: {str(e)}")
            logger.error(f"Erro ao visualizar dados pessoais: {str(e)}")
    
    def editar_dados_pessoais(self):
        try:
            if not self.usuario_atual:
                raise ValueError("Nenhum usuário logado.")
            
            dados = self.dados['usuarios'][self.usuario_atual]['dados_pessoais']
            
            print("\n--- EDITAR DADOS PESSOAIS ---")
            print("Deixe em branco para manter o valor atual")
            
            novo_nome = input(f"\nNome atual: {dados['nome']}\nNovo nome: ")
            if novo_nome:
                self._validar_entrada(novo_nome, "texto", min_len=5)
                dados['nome'] = novo_nome
            
            novo_email = input(f"\nEmail atual: {dados['email']}\nNovo email: ")
            if novo_email:
                self._validar_entrada(novo_email, "email")
                dados['email'] = novo_email
            
            nova_data = input(f"\nData de nascimento atual: {dados['data_nascimento']}\nNova data (DD/MM/AAAA): ")
            if nova_data:
                self._validar_entrada(nova_data, "data")
                dados['data_nascimento'] = nova_data
            
            self.salvar_dados()
            self._registrar_log_privacidade("Alteração de dados", f"Usuário {self.usuario_atual} alterou dados pessoais")
            print("\nDados atualizados com sucesso!")
            logger.info(f"Usuário {self.usuario_atual} atualizou dados pessoais")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao editar dados: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao editar dados.")
            logger.error(f"Erro inesperado ao editar dados: {str(e)}")
    
    def excluir_conta(self):
        try:
            if not self.usuario_atual:
                raise ValueError("Nenhum usuário logado.")
            
            confirmacao = input("\nATENÇÃO: Tem certeza que deseja excluir sua conta permanentemente? (s/n): ").lower()
            if confirmacao != 's':
                return
            
            # Anonimizar dados pessoais para conformidade com LGPD
            usuario = self.usuario_atual
            dados_pessoais = self.dados['usuarios'][usuario]['dados_pessoais']
            
            self.dados['usuarios'][usuario]['dados_pessoais'] = {
                "nome": "Usuário Excluído",
                "email": f"excluido_{usuario}@anonimo.com",
                "data_nascimento": "01/01/1900",
                "cpf": "000.000.000-00"
            }
            
            # Manter apenas informações essenciais para fins de auditoria
            self.dados['usuarios'][usuario]['ativo'] = False
            self.dados['usuarios'][usuario]['excluido_em'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            self.salvar_dados()
            self._registrar_log_privacidade("Exclusão de conta", f"Usuário {usuario} excluiu a conta")
            logger.info(f"Usuário {usuario} excluiu a conta")
            
            print("\nSua conta foi excluída com sucesso. Todos os dados pessoais foram anonimizados.")
            self.usuario_atual = None
        
        except Exception as e:
            print(f"\nErro ao excluir conta: {str(e)}")
            logger.error(f"Erro ao excluir conta: {str(e)}")
    
    # Funções compartilhadas
    def mostrar_perfil(self):
        try:
            if not self.usuario_atual:
                raise ValueError("Nenhum usuário logado.")
            
            usuario = self.usuario_atual
            user_info = self.dados['usuarios'][usuario]
            
            print("\n--- MEU PERFIL ---")
            print(f"Usuário: {usuario}")
            print(f"Tipo: {user_info['tipo'].capitalize()}")
            print(f"Data de cadastro: {user_info['data_cadastro']}")
            print(f"Último acesso: {user_info['ultimo_acesso']}")
            
            if user_info['tipo'] == 'aluno':
                print("\nCursos matriculados:")
                if user_info['cursos_matriculados']:
                    for curso in user_info['cursos_matriculados']:
                        print(f"- {curso}")
                else:
                    print("Nenhum curso matriculado.")
            else:
                print("\nCursos criados:")
                if user_info.get('cursos_criados', []):
                    for curso in user_info['cursos_criados']:
                        print(f"- {curso}")
                else:
                    print("Nenhum curso criado.")
            
            print("\n1. Visualizar dados pessoais")
            print("2. Editar dados pessoais")
            print("3. Excluir minha conta")
            print("4. Voltar")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == '1':
                self.visualizar_dados_pessoais()
            elif opcao == '2':
                self.editar_dados_pessoais()
            elif opcao == '3':
                self.excluir_conta()
            elif opcao == '4':
                return
            else:
                print("\nOpção inválida!")
        
        except Exception as e:
            print(f"\nErro: {str(e)}")
            logger.error(f"Erro ao mostrar perfil: {str(e)}")
    
    def visualizar_cursos_disponiveis(self):
        try:
            print("\n--- CURSOS DISPONÍVEIS ---")
            for nivel, cursos in self.dados['cursos'].items():
                print(f"\nNível: {nivel.capitalize()}")
                for nome_curso, detalhes in cursos.items():
                    print(f"\n- {nome_curso}")
                    print(f"  Descrição: {detalhes['descricao']}")
                    print(f"  Dificuldade: {detalhes['dificuldade']}")
                    print(f"  Professor: {detalhes.get('professor', 'Não definido')}")
                    print(f"  Lições: {len(detalhes.get('licoes', {}))}")
                    print(f"  Avaliações: {len(detalhes.get('avaliacoes', []))}")
                    print(f"  Avisos: {len(detalhes.get('avisos', []))}")
            
            input("\nPressione Enter para voltar...")
        
        except Exception as e:
            print(f"\nErro ao visualizar cursos: {str(e)}")
            logger.error(f"Erro ao visualizar cursos: {str(e)}")
    
    # Funções específicas para alunos
    def menu_aluno(self):
        try:
            while True:
                print(f"\n=== MENU DO ALUNO === [Usuário: {self.usuario_atual}]")
                print("1. Visualizar cursos disponíveis")
                print("2. Inscrever-se em um curso")
                print("3. Acessar conteúdo do curso")
                print("4. Ver histórico de progresso")
                print("5. Ver mensagens")
                print("6. Meu perfil")
                print("7. Sair")
                
                opcao = input("\nEscolha uma opção: ")
                
                try:
                    opcao = int(opcao)
                    
                    if opcao == 1:
                        self.visualizar_cursos_disponiveis()
                    elif opcao == 2:
                        self.inscrever_em_curso()
                    elif opcao == 3:
                        self.acessar_conteudo_curso()
                    elif opcao == 4:
                        self.ver_historico_progresso()
                    elif opcao == 5:
                        self.ver_mensagens()
                    elif opcao == 6:
                        self.mostrar_perfil()
                    elif opcao == 7:
                        self.sair()
                        break
                    else:
                        print("\nOpção inválida!")
                except ValueError:
                    print("\nPor favor, digite apenas números!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no menu do aluno: {str(e)}")
            self.sair()
    
    def inscrever_em_curso(self):
        try:
            print("\n--- INSCRIÇÃO EM CURSOS ---")
            cursos_disponiveis = []
            
            for nivel in self.dados['cursos'].values():
                for nome_curso in nivel.keys():
                    cursos_disponiveis.append(nome_curso)
            
            if not cursos_disponiveis:
                print("Nenhum curso disponível no momento.")
                return
            
            print("Cursos disponíveis para inscrição:")
            for i, curso in enumerate(cursos_disponiveis, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja se inscrever (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_disponiveis)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_disponiveis[escolha-1]
            
            if curso_selecionado in self.dados['usuarios'][self.usuario_atual]['cursos_matriculados']:
                raise ValueError("Você já está matriculado neste curso!")
            
            self.dados['usuarios'][self.usuario_atual]['cursos_matriculados'].append(curso_selecionado)
            self.dados['usuarios'][self.usuario_atual]['progresso'][curso_selecionado] = {
                "licoes_concluidas": 0,
                "total_licoes": sum(len(nivel.get(curso_selecionado, {}).get('licoes', {})) 
                                for nivel in self.dados['cursos'].values() 
                                if curso_selecionado in nivel),
                "avaliacoes": {}
            }
            
            self.salvar_dados()
            self._registrar_log_privacidade("Inscrição em curso", f"Usuário {self.usuario_atual} se inscreveu no curso {curso_selecionado}")
            print(f"\nInscrição no curso '{curso_selecionado}' realizada com sucesso!")
            logger.info(f"Usuário {self.usuario_atual} se inscreveu no curso {curso_selecionado}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro na inscrição: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado durante a inscrição.")
            logger.error(f"Erro inesperado na inscrição: {str(e)}")
    
    def acessar_conteudo_curso(self):
        try:
            print("\n--- ACESSAR CONTEÚDO DO CURSO ---")
            cursos_matriculados = self.dados['usuarios'][self.usuario_atual]['cursos_matriculados']
            
            if not cursos_matriculados:
                print("\nVocê não está matriculado em nenhum curso.")
                return
            
            print("\nSeus cursos matriculados:")
            for i, curso in enumerate(cursos_matriculados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja acessar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_matriculados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_matriculados[escolha-1]
            curso_info = None
            
            for nivel in self.dados['cursos'].values():
                if curso_selecionado in nivel:
                    curso_info = nivel[curso_selecionado]
                    break
            
            if not curso_info:
                raise ValueError("Curso não encontrado!")
            
            self.menu_curso_aluno(curso_selecionado, curso_info)
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao acessar curso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao acessar o curso.")
            logger.error(f"Erro inesperado ao acessar curso: {str(e)}")
    
    def menu_curso_aluno(self, curso_selecionado, curso_info):
        try:
            while True:
                total_licoes = len(curso_info['licoes'])
                concluidas = self.dados['usuarios'][self.usuario_atual]['progresso'][curso_selecionado]['licoes_concluidas']
                progresso = (concluidas / total_licoes) * 100 if total_licoes > 0 else 0
                
                print(f"\n--- {curso_selecionado} ---")
                print(f"Progresso: {progresso:.1f}%")
                print("\n1. Listar lições")
                print("2. Acessar lição")
                print("3. Realizar avaliação")
                print("4. Ver histórico")
                print("5. Ver avisos")
                print("6. Voltar")
                
                opcao = input("\nEscolha uma opção: ")
                
                if opcao == '1':
                    print("\nLições disponíveis:")
                    for nome_licao, detalhes in curso_info['licoes'].items():
                        status = "✓" if detalhes['concluida'] else " "
                        print(f"[{status}] {nome_licao}")
                
                elif opcao == '2':
                    self.acessar_licao(curso_selecionado, curso_info)
                
                elif opcao == '3':
                    self.realizar_avaliacao(curso_selecionado, curso_info)
                
                elif opcao == '4':
                    self.ver_historico_curso(curso_selecionado)
                
                elif opcao == '5':
                    self.ver_avisos_curso(curso_info)
                
                elif opcao == '6':
                    break
                
                else:
                    print("\nOpção inválida!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no menu do curso: {str(e)}")
    
    def acessar_licao(self, curso_selecionado, curso_info):
        try:
            print("\nLições disponíveis:")
            licoes = list(curso_info['licoes'].items())
            for i, (nome_licao, detalhes) in enumerate(licoes, 1):
                print(f"{i}. {nome_licao}")
            
            licao_escolha = input("\nDigite o número da lição que deseja acessar: ")
            licao_escolha = int(self._validar_entrada(licao_escolha, "numero", opcoes=[str(i) for i in range(1, len(licoes)+1)]))
            
            nome_licao, detalhes = licoes[licao_escolha-1]
            
            print(f"\n=== {nome_licao} ===")
            print(detalhes['conteudo'])
            
            if not detalhes['concluida']:
                marcar = input("\nDeseja marcar esta lição como concluída? (s/n): ").lower()
                if marcar == 's':
                    curso_info['licoes'][nome_licao]['concluida'] = True
                    self.dados['usuarios'][self.usuario_atual]['progresso'][curso_selecionado]['licoes_concluidas'] += 1
                    self.salvar_dados()
                    self._registrar_log_privacidade("Conclusão de lição", f"Usuário {self.usuario_atual} concluiu lição {nome_licao} no curso {curso_selecionado}")
                    print("\nLição marcada como concluída!")
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao acessar lição: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao acessar a lição.")
            logger.error(f"Erro inesperado ao acessar lição: {str(e)}")
    
    def realizar_avaliacao(self, curso_selecionado, curso_info):
        try:
            if not curso_info['avaliacoes']:
                print("\nEste curso não possui avaliações no momento.")
                return
            
            print("\nAvaliações disponíveis:")
            for i, avaliacao in enumerate(curso_info['avaliacoes'], 1):
                print(f"\n{i}. {avaliacao['titulo']}")
                print(f"   Perguntas: {len(avaliacao['perguntas'])}")
            
            avaliacao_escolha = input("\nDigite o número da avaliação que deseja realizar (ou 0 para cancelar): ")
            avaliacao_escolha = int(self._validar_entrada(avaliacao_escolha, "numero", opcoes=[str(i) for i in range(len(curso_info['avaliacoes'])+1)]))
            
            if avaliacao_escolha == 0:
                return
            
            avaliacao = curso_info['avaliacoes'][avaliacao_escolha-1]
            acertos = 0
            
            for pergunta in avaliacao['perguntas']:
                print(f"\nPergunta: {pergunta['pergunta']}")
                for j, opcao in enumerate(pergunta['opcoes']):
                    print(f"{j+1}. {opcao}")
                
                resposta = input("\nDigite o número da sua resposta: ")
                resposta = int(self._validar_entrada(resposta, "numero", opcoes=[str(i) for i in range(1, len(pergunta['opcoes'])+1)])) - 1
                
                if resposta == pergunta['resposta']:
                    print("\nResposta correta!")
                    acertos += 1
                else:
                    print(f"\nResposta incorreta. A correta era: {pergunta['opcoes'][pergunta['resposta']]}")
            
            nota = (acertos / len(avaliacao['perguntas'])) * 100
            print(f"\nVocê acertou {acertos} de {len(avaliacao['perguntas'])} perguntas.")
            print(f"Nota: {nota:.1f}%")
            
            # Registrar a avaliação no progresso
            self.dados['usuarios'][self.usuario_atual]['progresso'][curso_selecionado]['avaliacoes'][avaliacao['titulo']] = nota
            self.salvar_dados()
            self._registrar_log_privacidade("Realização de avaliação", f"Usuário {self.usuario_atual} realizou avaliação {avaliacao['titulo']} no curso {curso_selecionado} e obteve nota {nota:.1f}%")
            logger.info(f"Usuário {self.usuario_atual} realizou avaliação no curso {curso_selecionado}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro na avaliação: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado durante a avaliação.")
            logger.error(f"Erro inesperado na avaliação: {str(e)}")
    
    def ver_historico_curso(self, curso_selecionado):
        try:
            progresso_curso = self.dados['usuarios'][self.usuario_atual]['progresso'][curso_selecionado]
            total_licoes = progresso_curso['total_licoes']
            concluidas = progresso_curso['licoes_concluidas']
            progresso = (concluidas / total_licoes) * 100 if total_licoes > 0 else 0
            
            print(f"\n--- HISTÓRICO DE PROGRESSO: {curso_selecionado} ---")
            print(f"Progresso geral: {progresso:.1f}%")
            print(f"Lições concluídas: {concluidas}/{total_licoes}")
            
            if progresso_curso['avaliacoes']:
                print("\nAvaliações realizadas:")
                for avaliacao, nota in progresso_curso['avaliacoes'].items():
                    print(f"- {avaliacao}: {nota:.1f}%")
            else:
                print("\nNenhuma avaliação realizada ainda.")
            
            input("\nPressione Enter para voltar...")
        except Exception as e:
            print(f"\nErro ao ver histórico: {str(e)}")
            logger.error(f"Erro ao ver histórico: {str(e)}")
    
    def ver_avisos_curso(self, curso_info):
        try:
            if not curso_info['avisos']:
                print("\nNenhum aviso disponível para este curso.")
                return
            
            print("\n--- AVISOS DO CURSO ---")
            for aviso in curso_info['avisos']:
                print(f"\nData: {aviso['data']}")
                print(f"Título: {aviso['titulo']}")
                print(f"Mensagem: {aviso['mensagem']}")
                print(f"Autor: {aviso.get('autor', 'Sistema')}")
            
            input("\nPressione Enter para voltar...")
        except Exception as e:
            print(f"\nErro ao ver avisos: {str(e)}")
            logger.error(f"Erro ao ver avisos: {str(e)}")
    
    def ver_historico_progresso(self):
        try:
            progresso_geral = self.dados['usuarios'][self.usuario_atual]['progresso']
            
            if not progresso_geral:
                print("\nVocê não está matriculado em nenhum curso.")
                return
            
            print("\n--- HISTÓRICO DE PROGRESSO ---")
            for curso, dados in progresso_geral.items():
                total_licoes = dados['total_licoes']
                concluidas = dados['licoes_concluidas']
                progresso = (concluidas / total_licoes) * 100 if total_licoes > 0 else 0
                
                print(f"\nCurso: {curso}")
                print(f"Progresso: {progresso:.1f}%")
                print(f"Lições concluídas: {concluidas}/{total_licoes}")
                
                if dados['avaliacoes']:
                    print("Avaliações realizadas:")
                    for avaliacao, nota in dados['avaliacoes'].items():
                        print(f"- {avaliacao}: {nota:.1f}%")
            
            input("\nPressione Enter para voltar...")
        except Exception as e:
            print(f"\nErro ao ver progresso: {str(e)}")
            logger.error(f"Erro ao ver progresso: {str(e)}")
    
    def ver_mensagens(self):
        try:
            mensagens = self.dados['usuarios'][self.usuario_atual]['mensagens']
            
            if not mensagens:
                print("\nNenhuma mensagem disponível.")
                return
            
            print("\n--- SUAS MENSAGENS ---")
            for curso, msgs in mensagens.items():
                print(f"\nCurso: {curso if curso else 'Geral'}")
                for msg in msgs:
                    print(f"\nData: {msg['data']}")
                    print(f"De: {msg['de']}")
                    print(f"Mensagem: {msg['mensagem']}")
            
            input("\nPressione Enter para voltar...")
        except Exception as e:
            print(f"\nErro ao ver mensagens: {str(e)}")
            logger.error(f"Erro ao ver mensagens: {str(e)}")
    
    # Funções específicas para professores
    def menu_professor(self):
        try:
            while True:
                print(f"\n=== MENU DO PROFESSOR === [Usuário: {self.usuario_atual}]")
                print("1. Gerenciar cursos")
                print("2. Gerenciar conteúdo das aulas")
                print("3. Gerenciar avaliações")
                print("4. Visualizar progresso dos alunos")
                print("5. Enviar mensagens/avisos")
                print("6. Meu perfil")
                print("7. Sair")
                
                opcao = input("\nEscolha uma opção: ")
                
                try:
                    opcao = int(opcao)
                    
                    if opcao == 1:
                        self.gerenciar_cursos()
                    elif opcao == 2:
                        self.gerenciar_conteudo_aulas()
                    elif opcao == 3:
                        self.gerenciar_avaliacoes()
                    elif opcao == 4:
                        self.visualizar_progresso_alunos()
                    elif opcao == 5:
                        self.enviar_mensagens_avisos()
                    elif opcao == 6:
                        self.mostrar_perfil()
                    elif opcao == 7:
                        self.sair()
                        break
                    else:
                        print("\nOpção inválida!")
                except ValueError:
                    print("\nPor favor, digite apenas números!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no menu do professor: {str(e)}")
            self.sair()
    
    def gerenciar_cursos(self):
        try:
            while True:
                print("\n--- GERENCIAR CURSOS ---")
                print("1. Criar novo curso")
                print("2. Editar curso existente")
                print("3. Excluir curso")
                print("4. Voltar")
                
                opcao = input("\nEscolha uma opção: ")
                
                try:
                    opcao = int(opcao)
                    
                    if opcao == 1:
                        self.criar_curso()
                    elif opcao == 2:
                        self.editar_curso()
                    elif opcao == 3:
                        self.excluir_curso()
                    elif opcao == 4:
                        break
                    else:
                        print("\nOpção inválida!")
                except ValueError:
                    print("\nPor favor, digite apenas números!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no gerenciamento de cursos: {str(e)}")
    
    def criar_curso(self):
        try:
            print("\n--- CRIAR NOVO CURSO ---")
            print("Níveis disponíveis: iniciante, intermediario, avancado")
            nivel = input("Digite o nível do novo curso: ").lower()
            self._validar_entrada(nivel, "opcao", opcoes=["iniciante", "intermediario", "avancado"])
            
            nome_curso = input("Digite o nome do novo curso: ")
            self._validar_entrada(nome_curso, "texto", min_len=5, max_len=50)
            
            if any(nome_curso in cursos for cursos in self.dados['cursos'].values()):
                raise ValueError("Já existe um curso com este nome!")
            
            descricao = input("Digite a descrição do curso: ")
            self._validar_entrada(descricao, "texto", min_len=10, max_len=200)
            
            dificuldade = input("Digite o nível de dificuldade (Fácil, Médio, Difícil): ")
            self._validar_entrada(dificuldade, "opcao", opcoes=["Fácil", "Médio", "Difícil"])
            
            self.dados['cursos'][nivel][nome_curso] = {
                "descricao": descricao,
                "dificuldade": dificuldade,
                "professor": self.usuario_atual,
                "licoes": {},
                "avaliacoes": [],
                "avisos": []
            }
            
            # Adicionar ao perfil do professor
            self.dados['usuarios'][self.usuario_atual]['cursos_criados'].append(nome_curso)
            
            self.salvar_dados()
            self._registrar_log_privacidade("Criação de curso", f"Professor {self.usuario_atual} criou o curso {nome_curso}")
            print("\nCurso criado com sucesso!")
            logger.info(f"Curso {nome_curso} criado por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao criar curso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao criar o curso.")
            logger.error(f"Erro inesperado ao criar curso: {str(e)}")
    
    def editar_curso(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja editar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            curso_info = None
            nivel_curso = None
            
            for nivel, cursos in self.dados['cursos'].items():
                if curso_selecionado in cursos:
                    curso_info = cursos[curso_selecionado]
                    nivel_curso = nivel
                    break
            
            if not curso_info:
                raise ValueError("Curso não encontrado!")
            
            print("\nEditando curso:")
            print(f"1. Nome atual: {curso_selecionado}")
            print(f"2. Descrição: {curso_info['descricao']}")
            print(f"3. Dificuldade: {curso_info['dificuldade']}")
            print(f"4. Nível: {nivel_curso}")
            print("5. Cancelar")
            
            opcao = input("\nO que deseja editar? (1-4) ou 5 para cancelar: ")
            
            if opcao == '1':
                novo_nome = input("\nNovo nome do curso: ")
                self._validar_entrada(novo_nome, "texto", min_len=5, max_len=50)
                
                if novo_nome != curso_selecionado and any(novo_nome in cursos for cursos in self.dados['cursos'].values()):
                    raise ValueError("Já existe um curso com este nome!")
                
                # Atualizar em todas as estruturas
                self.dados['cursos'][nivel_curso][novo_nome] = self.dados['cursos'][nivel_curso].pop(curso_selecionado)
                
                # Atualizar na lista de cursos criados
                index = self.dados['usuarios'][self.usuario_atual]['cursos_criados'].index(curso_selecionado)
                self.dados['usuarios'][self.usuario_atual]['cursos_criados'][index] = novo_nome
                
                # Atualizar nos alunos matriculados
                for usuario in self.dados['usuarios'].values():
                    if curso_selecionado in usuario.get('cursos_matriculados', []):
                        index = usuario['cursos_matriculados'].index(curso_selecionado)
                        usuario['cursos_matriculados'][index] = novo_nome
                    
                    if curso_selecionado in usuario.get('progresso', {}):
                        usuario['progresso'][novo_nome] = usuario['progresso'].pop(curso_selecionado)
                
                self._registrar_log_privacidade("Alteração de curso", f"Professor {self.usuario_atual} alterou nome do curso de {curso_selecionado} para {novo_nome}")
                print("\nNome do curso atualizado com sucesso!")
                logger.info(f"Curso {curso_selecionado} renomeado para {novo_nome}")
            
            elif opcao == '2':
                nova_descricao = input("\nNova descrição: ")
                self._validar_entrada(nova_descricao, "texto", min_len=10, max_len=200)
                curso_info['descricao'] = nova_descricao
                self._registrar_log_privacidade("Alteração de curso", f"Professor {self.usuario_atual} alterou descrição do curso {curso_selecionado}")
                print("\nDescrição atualizada!")
            
            elif opcao == '3':
                nova_dificuldade = input("\nNova dificuldade (Fácil, Médio, Difícil): ")
                self._validar_entrada(nova_dificuldade, "opcao", opcoes=["Fácil", "Médio", "Difícil"])
                curso_info['dificuldade'] = nova_dificuldade
                self._registrar_log_privacidade("Alteração de curso", f"Professor {self.usuario_atual} alterou dificuldade do curso {curso_selecionado}")
                print("\nDificuldade atualizada!")
            
            elif opcao == '4':
                print("\nNíveis disponíveis: iniciante, intermediario, avancado")
                novo_nivel = input("Novo nível: ").lower()
                self._validar_entrada(novo_nivel, "opcao", opcoes=["iniciante", "intermediario", "avancado"])
                
                if novo_nivel != nivel_curso:
                    self.dados['cursos'][novo_nivel][curso_selecionado] = self.dados['cursos'][nivel_curso].pop(curso_selecionado)
                    self._registrar_log_privacidade("Alteração de curso", f"Professor {self.usuario_atual} alterou nível do curso {curso_selecionado} de {nivel_curso} para {novo_nivel}")
                    print("\nNível do curso atualizado com sucesso!")
                    logger.info(f"Nível do curso {curso_selecionado} alterado para {novo_nivel}")
            
            elif opcao == '5':
                return
            
            else:
                print("\nOpção inválida!")
            
            self.salvar_dados()
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao editar curso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao editar o curso.")
            logger.error(f"Erro inesperado ao editar curso: {str(e)}")
    
    def excluir_curso(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja excluir (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            
            confirmacao = input(f"\nTem certeza que deseja excluir o curso '{curso_selecionado}'? (s/n): ").lower()
            if confirmacao != 's':
                return
            
            # Remover o curso de todas as estruturas
            for nivel in self.dados['cursos'].values():
                if curso_selecionado in nivel:
                    nivel.pop(curso_selecionado)
                    break
            
            # Remover da lista de cursos criados
            self.dados['usuarios'][self.usuario_atual]['cursos_criados'].remove(curso_selecionado)
            
            # Remover dos alunos matriculados
            for usuario in self.dados['usuarios'].values():
                if curso_selecionado in usuario.get('cursos_matriculados', []):
                    usuario['cursos_matriculados'].remove(curso_selecionado)
                
                if curso_selecionado in usuario.get('progresso', {}):
                    usuario['progresso'].pop(curso_selecionado)
            
            self.salvar_dados()
            self._registrar_log_privacidade("Exclusão de curso", f"Professor {self.usuario_atual} excluiu o curso {curso_selecionado}")
            print("\nCurso excluído com sucesso!")
            logger.info(f"Curso {curso_selecionado} excluído por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao excluir curso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao excluir o curso.")
            logger.error(f"Erro inesperado ao excluir curso: {str(e)}")
    
    def gerenciar_conteudo_aulas(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja gerenciar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            curso_info = None
            
            for nivel in self.dados['cursos'].values():
                if curso_selecionado in nivel:
                    curso_info = nivel[curso_selecionado]
                    break
            
            if not curso_info:
                raise ValueError("Curso não encontrado!")
            
            while True:
                print(f"\n--- GERENCIAR CONTEÚDO: {curso_selecionado} ---")
                print("1. Adicionar lição")
                print("2. Editar lição")
                print("3. Remover lição")
                print("4. Voltar")
                
                opcao = input("\nEscolha uma opção: ")
                
                if opcao == '1':
                    self.adicionar_licao(curso_info)
                elif opcao == '2':
                    self.editar_licao(curso_info)
                elif opcao == '3':
                    self.remover_licao(curso_info)
                elif opcao == '4':
                    break
                else:
                    print("\nOpção inválida!")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro no gerenciamento de conteúdo: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao gerenciar o conteúdo.")
            logger.error(f"Erro inesperado no gerenciamento de conteúdo: {str(e)}")
    
    def adicionar_licao(self, curso_info):
        try:
            print("\n--- ADICIONAR LIÇÃO ---")
            nome_licao = input("Nome da nova lição: ")
            self._validar_entrada(nome_licao, "texto", min_len=3, max_len=50)
            
            conteudo = input("Conteúdo da lição: ")
            self._validar_entrada(conteudo, "texto", min_len=10)
            
            curso_info['licoes'][nome_licao] = {
                "conteudo": conteudo,
                "concluida": False
            }
            
            # Atualizar contagem total de lições para alunos matriculados
            for usuario in self.dados['usuarios'].values():
                if curso_info['professor'] + curso_info['descricao'] in usuario.get('progresso', {}):
                    usuario['progresso'][curso_info['professor'] + curso_info['descricao']]['total_licoes'] += 1
            
            self.salvar_dados()
            self._registrar_log_privacidade("Adição de lição", f"Professor {self.usuario_atual} adicionou lição {nome_licao}")
            print("\nLição adicionada com sucesso!")
            logger.info(f"Luição {nome_licao} adicionada por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao adicionar lição: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao adicionar a lição.")
            logger.error(f"Erro inesperado ao adicionar lição: {str(e)}")
    
    def editar_licao(self, curso_info):
        try:
            if not curso_info['licoes']:
                print("\nEste curso não possui lições ainda.")
                return
            
            print("\nLições disponíveis:")
            licoes = list(curso_info['licoes'].items())
            for i, (nome_licao, _) in enumerate(licoes, 1):
                print(f"{i}. {nome_licao}")
            
            escolha = input("\nDigite o número da lição que deseja editar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(licoes)+1)]))
            
            if escolha == 0:
                return
            
            nome_licao, _ = licoes[escolha-1]
            novo_nome = input(f"\nNovo nome para a lição (atual: {nome_licao}): ") or nome_licao
            self._validar_entrada(novo_nome, "texto", min_len=3, max_len=50)
            
            novo_conteudo = input("Novo conteúdo: ") or curso_info['licoes'][nome_licao]['conteudo']
            self._validar_entrada(novo_conteudo, "texto", min_len=10)
            
            if novo_nome != nome_licao:
                curso_info['licoes'][novo_nome] = curso_info['licoes'].pop(nome_licao)
            
            curso_info['licoes'][novo_nome]['conteudo'] = novo_conteudo
            self.salvar_dados()
            self._registrar_log_privacidade("Edição de lição", f"Professor {self.usuario_atual} editou lição {nome_licao}")
            print("\nLição atualizada com sucesso!")
            logger.info(f"Lição {nome_licao} editada por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao editar lição: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao editar a lição.")
            logger.error(f"Erro inesperado ao editar lição: {str(e)}")
    
    def remover_licao(self, curso_info):
        try:
            if not curso_info['licoes']:
                print("\nEste curso não possui lições ainda.")
                return
            
            print("\nLições disponíveis:")
            licoes = list(curso_info['licoes'].items())
            for i, (nome_licao, _) in enumerate(licoes, 1):
                print(f"{i}. {nome_licao}")
            
            escolha = input("\nDigite o número da lição que deseja remover (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(licoes)+1)]))
            
            if escolha == 0:
                return
            
            nome_licao, _ = licoes[escolha-1]
            
            confirmacao = input(f"\nTem certeza que deseja remover a lição '{nome_licao}'? (s/n): ").lower()
            if confirmacao != 's':
                return
            
            # Verificar se a lição estava concluída para atualizar o progresso dos alunos
            if curso_info['licoes'][nome_licao]['concluida']:
                for usuario in self.dados['usuarios'].values():
                    if curso_info['professor'] + curso_info['descricao'] in usuario.get('progresso', {}):
                        usuario['progresso'][curso_info['professor'] + curso_info['descricao']]['licoes_concluidas'] -= 1
            
            # Remover a lição
            curso_info['licoes'].pop(nome_licao)
            
            # Atualizar contagem total de lições para alunos matriculados
            for usuario in self.dados['usuarios'].values():
                if curso_info['professor'] + curso_info['descricao'] in usuario.get('progresso', {}):
                    usuario['progresso'][curso_info['professor'] + curso_info['descricao']]['total_licoes'] -= 1
            
            self.salvar_dados()
            self._registrar_log_privacidade("Remoção de lição", f"Professor {self.usuario_atual} removeu lição {nome_licao}")
            print("\nLição removida com sucesso!")
            logger.info(f"Lição {nome_licao} removida por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao remover lição: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao remover a lição.")
            logger.error(f"Erro inesperado ao remover lição: {str(e)}")
    
    def gerenciar_avaliacoes(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso que deseja gerenciar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            curso_info = None
            
            for nivel in self.dados['cursos'].values():
                if curso_selecionado in nivel:
                    curso_info = nivel[curso_selecionado]
                    break
            
            if not curso_info:
                raise ValueError("Curso não encontrado!")
            
            while True:
                print(f"\n--- GERENCIAR AVALIAÇÕES: {curso_selecionado} ---")
                print("1. Criar nova avaliação")
                print("2. Editar avaliação existente")
                print("3. Excluir avaliação")
                print("4. Voltar")
                
                opcao = input("\nEscolha uma opção: ")
                
                if opcao == '1':
                    self.criar_avaliacao(curso_info)
                elif opcao == '2':
                    self.editar_avaliacao(curso_info)
                elif opcao == '3':
                    self.excluir_avaliacao(curso_info)
                elif opcao == '4':
                    break
                else:
                    print("\nOpção inválida!")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro no gerenciamento de avaliações: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao gerenciar avaliações.")
            logger.error(f"Erro inesperado no gerenciamento de avaliações: {str(e)}")
    
    def criar_avaliacao(self, curso_info):
        try:
            print("\n--- CRIAR AVALIAÇÃO ---")
            titulo = input("Título da avaliação: ")
            self._validar_entrada(titulo, "texto", min_len=5, max_len=50)
            
            avaliacao = {
                "titulo": titulo,
                "perguntas": []
            }
            
            while True:
                print("\n1. Adicionar pergunta")
                print("2. Finalizar e salvar")
                print("3. Cancelar")
                
                opcao = input("\nEscolha uma opção: ")
                
                if opcao == '1':
                    pergunta = input("\nDigite a pergunta: ")
                    self._validar_entrada(pergunta, "texto", min_len=10)
                    
                    opcoes = []
                    for i in range(3):
                        opcao_texto = input(f"Opção {i+1}: ")
                        self._validar_entrada(opcao_texto, "texto", min_len=1)
                        opcoes.append(opcao_texto)
                    
                    resposta = input("Número da opção correta (1-3): ")
                    resposta = int(self._validar_entrada(resposta, "numero", opcoes=["1", "2", "3"])) - 1
                    
                    avaliacao['perguntas'].append({
                        "pergunta": pergunta,
                        "opcoes": opcoes,
                        "resposta": resposta
                    })
                    
                    print("\nPergunta adicionada!")
                
                elif opcao == '2':
                    if not avaliacao['perguntas']:
                        print("\nA avaliação precisa ter pelo menos uma pergunta!")
                        continue
                    
                    curso_info['avaliacoes'].append(avaliacao)
                    self.salvar_dados()
                    self._registrar_log_privacidade("Criação de avaliação", f"Professor {self.usuario_atual} criou avaliação {titulo}")
                    print("\nAvaliação criada com sucesso!")
                    logger.info(f"Avaliação {titulo} criada por {self.usuario_atual}")
                    break
                
                elif opcao == '3':
                    confirmacao = input("\nTem certeza que deseja cancelar? Todas as perguntas serão perdidas. (s/n): ").lower()
                    if confirmacao == 's':
                        return
                else:
                    print("\nOpção inválida!")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao criar avaliação: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao criar a avaliação.")
            logger.error(f"Erro inesperado ao criar avaliação: {str(e)}")
    
    def editar_avaliacao(self, curso_info):
        try:
            if not curso_info['avaliacoes']:
                print("\nEste curso não possui avaliações ainda.")
                return
            
            print("\nAvaliações disponíveis:")
            for i, avaliacao in enumerate(curso_info['avaliacoes'], 1):
                print(f"{i}. {avaliacao['titulo']} ({len(avaliacao['perguntas'])} perguntas)")
            
            escolha = input("\nDigite o número da avaliação que deseja editar (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(curso_info['avaliacoes'])+1)]))
            
            if escolha == 0:
                return
            
            avaliacao = curso_info['avaliacoes'][escolha-1]
            
            while True:
                print(f"\n--- EDITANDO: {avaliacao['titulo']} ---")
                print("1. Editar título")
                print("2. Adicionar pergunta")
                print("3. Editar pergunta existente")
                print("4. Remover pergunta")
                print("5. Salvar alterações")
                print("6. Cancelar")
                
                opcao = input("\nEscolha uma opção: ")
                
                if opcao == '1':
                    novo_titulo = input("\nNovo título: ")
                    self._validar_entrada(novo_titulo, "texto", min_len=5, max_len=50)
                    avaliacao['titulo'] = novo_titulo
                    print("\nTítulo atualizado!")
                
                elif opcao == '2':
                    pergunta = input("\nDigite a pergunta: ")
                    self._validar_entrada(pergunta, "texto", min_len=10)
                    
                    opcoes = []
                    for i in range(3):
                        opcao_texto = input(f"Opção {i+1}: ")
                        self._validar_entrada(opcao_texto, "texto", min_len=1)
                        opcoes.append(opcao_texto)
                    
                    resposta = input("Número da opção correta (1-3): ")
                    resposta = int(self._validar_entrada(resposta, "numero", opcoes=["1", "2", "3"])) - 1
                    
                    avaliacao['perguntas'].append({
                        "pergunta": pergunta,
                        "opcoes": opcoes,
                        "resposta": resposta
                    })
                    
                    print("\nPergunta adicionada!")
                
                elif opcao == '3':
                    if not avaliacao['perguntas']:
                        print("\nNão há perguntas para editar.")
                        continue
                    
                    print("\nPerguntas disponíveis:")
                    for i, pergunta in enumerate(avaliacao['perguntas'], 1):
                        print(f"{i}. {pergunta['pergunta']}")
                    
                    pergunta_escolha = input("\nDigite o número da pergunta que deseja editar (ou 0 para cancelar): ")
                    pergunta_escolha = int(self._validar_entrada(pergunta_escolha, "numero", opcoes=[str(i) for i in range(len(avaliacao['perguntas'])+1)]))
                    
                    if pergunta_escolha == 0:
                        continue
                    
                    pergunta = avaliacao['perguntas'][pergunta_escolha-1]
                    
                    nova_pergunta = input(f"\nNova pergunta (atual: {pergunta['pergunta']}): ") or pergunta['pergunta']
                    self._validar_entrada(nova_pergunta, "texto", min_len=10)
                    pergunta['pergunta'] = nova_pergunta
                    
                    print("\nOpções atuais:")
                    for j, opcao in enumerate(pergunta['opcoes']):
                        print(f"{j+1}. {opcao}")
                    
                    for j in range(3):
                        nova_opcao = input(f"\nNova opção {j+1} (atual: {pergunta['opcoes'][j]}): ") or pergunta['opcoes'][j]
                        self._validar_entrada(nova_opcao, "texto", min_len=1)
                        pergunta['opcoes'][j] = nova_opcao
                    
                    nova_resposta = input(f"\nNova resposta correta (atual: {pergunta['resposta']+1}): ")
                    if nova_resposta:
                        nova_resposta = int(self._validar_entrada(nova_resposta, "numero", opcoes=["1", "2", "3"])) - 1
                        pergunta['resposta'] = nova_resposta
                    
                    print("\nPergunta atualizada!")
                
                elif opcao == '4':
                    if not avaliacao['perguntas']:
                        print("\nNão há perguntas para remover.")
                        continue
                    
                    print("\nPerguntas disponíveis:")
                    for i, pergunta in enumerate(avaliacao['perguntas'], 1):
                        print(f"{i}. {pergunta['pergunta']}")
                    
                    pergunta_escolha = input("\nDigite o número da pergunta que deseja remover (ou 0 para cancelar): ")
                    pergunta_escolha = int(self._validar_entrada(pergunta_escolha, "numero", opcoes=[str(i) for i in range(len(avaliacao['perguntas'])+1)]))
                    
                    if pergunta_escolha == 0:
                        continue
                    
                    confirmacao = input("\nTem certeza que deseja remover esta pergunta? (s/n): ").lower()
                    if confirmacao == 's':
                        avaliacao['perguntas'].pop(pergunta_escolha-1)
                        print("\nPergunta removida!")
                
                elif opcao == '5':
                    self.salvar_dados()
                    self._registrar_log_privacidade("Edição de avaliação", f"Professor {self.usuario_atual} editou avaliação {avaliacao['titulo']}")
                    print("\nAlterações salvas!")
                    logger.info(f"Avaliação {avaliacao['titulo']} editada por {self.usuario_atual}")
                    break
                
                elif opcao == '6':
                    confirmacao = input("\nTem certeza que deseja cancelar? Todas as alterações não salvas serão perdidas. (s/n): ").lower()
                    if confirmacao == 's':
                        return
                else:
                    print("\nOpção inválida!")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao editar avaliação: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao editar a avaliação.")
            logger.error(f"Erro inesperado ao editar avaliação: {str(e)}")
    
    def excluir_avaliacao(self, curso_info):
        try:
            if not curso_info['avaliacoes']:
                print("\nEste curso não possui avaliações ainda.")
                return
            
            print("\nAvaliações disponíveis:")
            for i, avaliacao in enumerate(curso_info['avaliacoes'], 1):
                print(f"{i}. {avaliacao['titulo']} ({len(avaliacao['perguntas'])} perguntas)")
            
            escolha = input("\nDigite o número da avaliação que deseja excluir (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(curso_info['avaliacoes'])+1)]))
            
            if escolha == 0:
                return
            
            confirmacao = input("\nTem certeza que deseja excluir esta avaliação? (s/n): ").lower()
            if confirmacao == 's':
                titulo = curso_info['avaliacoes'][escolha-1]['titulo']
                curso_info['avaliacoes'].pop(escolha-1)
                self.salvar_dados()
                self._registrar_log_privacidade("Exclusão de avaliação", f"Professor {self.usuario_atual} excluiu avaliação {titulo}")
                print("\nAvaliação excluída com sucesso!")
                logger.info(f"Avaliação {titulo} excluída por {self.usuario_atual}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao excluir avaliação: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao excluir a avaliação.")
            logger.error(f"Erro inesperado ao excluir avaliação: {str(e)}")
    
    def visualizar_progresso_alunos(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso para ver o progresso dos alunos (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            
            alunos_matriculados = []
            for usuario, dados in self.dados['usuarios'].items():
                if dados['tipo'] == 'aluno' and curso_selecionado in dados['cursos_matriculados']:
                    alunos_matriculados.append(usuario)
            
            if not alunos_matriculados:
                print("\nNenhum aluno matriculado neste curso.")
                return
            
            print("\nAlunos matriculados:")
            for i, aluno in enumerate(alunos_matriculados, 1):
                print(f"{i}. {aluno}")
            
            aluno_escolha = input("\nDigite o número do aluno para ver detalhes (ou 0 para ver todos): ")
            aluno_escolha = int(self._validar_entrada(aluno_escolha, "numero", opcoes=[str(i) for i in range(len(alunos_matriculados)+1)]))
            
            if aluno_escolha == 0:
                print("\nProgresso de todos os alunos:")
                for aluno in alunos_matriculados:
                    progresso = self.dados['usuarios'][aluno]['progresso'][curso_selecionado]
                    total_licoes = progresso['total_licoes']
                    concluidas = progresso['licoes_concluidas']
                    porcentagem = (concluidas / total_licoes) * 100 if total_licoes > 0 else 0
                    
                    print(f"\nAluno: {aluno}")
                    print(f"Lições concluídas: {concluidas}/{total_licoes} ({porcentagem:.1f}%)")
                    
                    if progresso['avaliacoes']:
                        print("Avaliações realizadas:")
                        for avaliacao, nota in progresso['avaliacoes'].items():
                            print(f"- {avaliacao}: {nota:.1f}%")
            else:
                aluno = alunos_matriculados[aluno_escolha-1]
                progresso = self.dados['usuarios'][aluno]['progresso'][curso_selecionado]
                total_licoes = progresso['total_licoes']
                concluidas = progresso['licoes_concluidas']
                porcentagem = (concluidas / total_licoes) * 100 if total_licoes > 0 else 0
                
                print(f"\n--- PROGRESSO DE {aluno} ---")
                print(f"Lições concluídas: {concluidas}/{total_licoes} ({porcentagem:.1f}%)")
                
                if progresso['avaliacoes']:
                    print("\nAvaliações realizadas:")
                    for avaliacao, nota in progresso['avaliacoes'].items():
                        print(f"- {avaliacao}: {nota:.1f}%")
                else:
                    print("\nNenhuma avaliação realizada ainda.")
            
            input("\nPressione Enter para voltar...")
            self._registrar_log_privacidade("Visualização de progresso", f"Professor {self.usuario_atual} visualizou progresso no curso {curso_selecionado}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao visualizar progresso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao visualizar o progresso.")
            logger.error(f"Erro inesperado ao visualizar progresso: {str(e)}")
    
    def enviar_mensagens_avisos(self):
        try:
            print("\n--- ENVIAR MENSAGENS/AVISOS ---")
            print("1. Enviar mensagem para aluno específico")
            print("2. Postar aviso em um curso")
            print("3. Voltar")
            
            opcao = input("\nEscolha uma opção: ")
            
            try:
                opcao = int(opcao)
                
                if opcao == 1:
                    self.enviar_mensagem_aluno()
                elif opcao == 2:
                    self.postar_aviso_curso()
                elif opcao == 3:
                    return
                else:
                    print("\nOpção inválida!")
            except ValueError:
                print("\nPor favor, digite apenas números!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no envio de mensagens: {str(e)}")
    
    def enviar_mensagem_aluno(self):
        try:
            alunos = [usuario for usuario, dados in self.dados['usuarios'].items() if dados['tipo'] == 'aluno']
            
            if not alunos:
                print("\nNão há alunos cadastrados.")
                return
            
            print("\nAlunos disponíveis:")
            for i, aluno in enumerate(alunos, 1):
                print(f"{i}. {aluno}")
            
            escolha = input("\nDigite o número do aluno (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(alunos)+1)]))
            
            if escolha == 0:
                return
            
            aluno = alunos[escolha-1]
            mensagem = input("\nDigite sua mensagem: ")
            self._validar_entrada(mensagem, "texto", min_len=5)
            
            if 'mensagens' not in self.dados['usuarios'][aluno]:
                self.dados['usuarios'][aluno]['mensagens'] = {}
            
            curso = input("Associar a qual curso? (deixe em branco para geral): ")
            
            if curso not in self.dados['usuarios'][aluno]['mensagens']:
                self.dados['usuarios'][aluno]['mensagens'][curso] = []
            
            self.dados['usuarios'][aluno]['mensagens'][curso].append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "de": self.usuario_atual,
                "mensagem": mensagem
            })
            
            self.salvar_dados()
            self._registrar_log_privacidade("Envio de mensagem", f"Professor {self.usuario_atual} enviou mensagem para {aluno}")
            print("\nMensagem enviada com sucesso!")
            logger.info(f"Mensagem enviada de {self.usuario_atual} para {aluno}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao enviar mensagem: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao enviar a mensagem.")
            logger.error(f"Erro inesperado ao enviar mensagem: {str(e)}")
    
    def postar_aviso_curso(self):
        try:
            cursos_criados = self.dados['usuarios'][self.usuario_atual]['cursos_criados']
            
            if not cursos_criados:
                print("\nVocê não criou nenhum curso ainda.")
                return
            
            print("\nSeus cursos criados:")
            for i, curso in enumerate(cursos_criados, 1):
                print(f"{i}. {curso}")
            
            escolha = input("\nDigite o número do curso (ou 0 para cancelar): ")
            escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(cursos_criados)+1)]))
            
            if escolha == 0:
                return
            
            curso_selecionado = cursos_criados[escolha-1]
            curso_info = None
            
            for nivel in self.dados['cursos'].values():
                if curso_selecionado in nivel:
                    curso_info = nivel[curso_selecionado]
                    break
            
            if not curso_info:
                raise ValueError("Curso não encontrado!")
            
            titulo = input("\nTítulo do aviso: ")
            self._validar_entrada(titulo, "texto", min_len=5, max_len=50)
            
            mensagem = input("Mensagem: ")
            self._validar_entrada(mensagem, "texto", min_len=10)
            
            curso_info['avisos'].append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "titulo": titulo,
                "mensagem": mensagem,
                "autor": self.usuario_atual
            })
            
            self.salvar_dados()
            self._registrar_log_privacidade("Postagem de aviso", f"Professor {self.usuario_atual} postou aviso no curso {curso_selecionado}")
            print("\nAviso postado com sucesso!")
            logger.info(f"Aviso postado por {self.usuario_atual} no curso {curso_selecionado}")
        
        except ValueError as e:
            print(f"\nErro: {str(e)}")
            logger.warning(f"Erro ao postar aviso: {str(e)}")
        except Exception as e:
            print("\nOcorreu um erro inesperado ao postar o aviso.")
            logger.error(f"Erro inesperado ao postar aviso: {str(e)}")

    # Funções de administração/backup
    def menu_backup(self):
        try:
            while True:
                print("\n=== MENU DE BACKUP ===")
                print("1. Criar backup agora")
                print("2. Listar backups disponíveis")
                print("3. Restaurar backup")
                print("4. Voltar")
                
                opcao = input("\nEscolha uma opção: ")
                
                try:
                    opcao = int(opcao)
                    
                    if opcao == 1:
                        if BackupManager.criar_backup():
                            print("\nBackup criado com sucesso!")
                        else:
                            print("\nFalha ao criar backup.")
                    elif opcao == 2:
                        backups = BackupManager.listar_backups()
                        if not backups:
                            print("\nNenhum backup disponível.")
                        else:
                            print("\nBackups disponíveis:")
                            for i, backup in enumerate(backups, 1):
                                print(f"\n{i}. {backup['nome']}")
                                print(f"   Data: {backup['data']}")
                                print(f"   Tamanho: {backup['tamanho']}")
                    elif opcao == 3:
                        backups = BackupManager.listar_backups()
                        if not backups:
                            print("\nNenhum backup disponível para restaurar.")
                            continue
                        
                        print("\nBackups disponíveis:")
                        for i, backup in enumerate(backups, 1):
                            print(f"{i}. {backup['nome']} ({backup['data']})")
                        
                        escolha = input("\nDigite o número do backup que deseja restaurar (ou 0 para cancelar): ")
                        escolha = int(self._validar_entrada(escolha, "numero", opcoes=[str(i) for i in range(len(backups)+1)]))
                        
                        if escolha == 0:
                            continue
                        
                        backup_selecionado = backups[escolha-1]
                        confirmacao = input(f"\nTem certeza que deseja restaurar o backup '{backup_selecionado['nome']}'? (s/n): ").lower()
                        if confirmacao == 's':
                            if BackupManager.restaurar_backup(backup_selecionado['caminho']):
                                print("\nBackup restaurado com sucesso! Reinicie o sistema para aplicar as alterações.")
                                input("Pressione Enter para continuar...")
                                sys.exit(0)
                            else:
                                print("\nFalha ao restaurar backup.")
                    elif opcao == 4:
                        break
                    else:
                        print("\nOpção inválida!")
                except ValueError:
                    print("\nPor favor, digite apenas números!")
        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            logger.error(f"Erro no menu de backup: {str(e)}")

# Função principal
def main():
    try:
        plataforma = PlataformaEnsino()
        
        while True:
            print("\n=== PLATAFORMA DE ENSINO ONLINE ===")
            print("1. Fazer login")
            print("2. Cadastrar novo usuário")
            print("3. Visualizar cursos disponíveis")
            print("4. Backup do sistema")
            print("5. Sobre o sistema")
            print("6. Sair")
            
            opcao = input("\nEscolha uma opção: ")
            
            try:
                opcao = int(opcao)
                
                if opcao == 1:
                    if plataforma.fazer_login():
                        if plataforma.dados['usuarios'][plataforma.usuario_atual]['tipo'] == 'professor':
                            plataforma.menu_professor()
                        else:
                            plataforma.menu_aluno()
                elif opcao == 2:
                    plataforma.cadastrar_usuario()
                elif opcao == 3:
                    plataforma.visualizar_cursos_disponiveis()
                elif opcao == 4:
                    plataforma.menu_backup()
                elif opcao == 5:
                    print("\n--- SOBRE O SISTEMA ---")
                    print("Plataforma de ensino online completa")
                    print("Desenvolvido para o projeto de Python")
                    print("Versão 5.0 - Com sistema de backup robusto")
                    input("\nPressione Enter para voltar...")
                elif opcao == 6:
                    print("\nObrigado por usar nossa plataforma. Até logo!")
                    break
                else:
                    print("\nOpção inválida. Tente novamente.")
            except ValueError:
                print("\nPor favor, digite apenas números.")
    
    except Exception as e:
        print(f"\nErro crítico: {str(e)}")
        logger.critical(f"Erro crítico no sistema: {str(e)}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()