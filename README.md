# Luxo Mundo Pet

Protótipo acadêmico para o Projeto Integrador – Laboratório de Programação (UNISA).

## Execução

Requer Python 3.10 ou superior, com biblioteca padrão e SQLite disponíveis.
No Windows, extraia o pacote e abra `INICIAR_WINDOWS.bat`.
Alternativamente execute `python iniciar.py` ou `python3 iniciar.py`.
O iniciador configura o servidor local, define a senha demonstrativa e abre o navegador.

- Loja: http://127.0.0.1:8080
- Administração: http://127.0.0.1:8080/admin
- Senha demonstrativa do iniciador: `GrupoPet2026!`
- Encerrar: Ctrl+C no terminal.

## Organização

- `app.py`: servidor HTTP, regras de negócio e interface HTML/CSS/JavaScript.
- `iniciar.py`: inicialização simplificada para demonstração local.
- `INICIAR_WINDOWS.bat`: atalho de execução no Windows.
- `LEIA_PRIMEIRO.txt`: instruções para o grupo.
- `loja.db`: criado automaticamente ao executar, com produtos demonstrativos.

A interface está incorporada em `app.py`; não existem arquivos de interface faltando.

## Funcionalidades

Catálogo, carrinho no armazenamento do navegador, envio de pedidos, baixa de estoque,
cadastro de produtos, atualização de quantidades e registro de mensagens de suporte.
O painel consulta pedidos e mensagens. Pagamentos e fretes são combinados fora do sistema.

## Modelo de dados

- `products`: nome, categoria, preço em centavos, quantidade e descrição.
- `orders`: cliente, telefone, endereço, total e data.
- `order_items`: itens e preços registrados em cada pedido.
- `tickets`: nome, contato, assunto, mensagem e data.

O pedido é validado no servidor e gravado em uma transação com a redução do estoque.
O banco fica na mesma pasta de `app.py`. Use dados fictícios nas demonstrações.

## Roteiro de validação

1. Consulte um produto e anote o estoque inicial.
2. Solicite uma unidade e confirme a mensagem com o número do pedido.
3. Entre no painel e confira o pedido, o total e a redução de uma unidade.
4. Envie uma mensagem de suporte e confira o registro no painel.
5. Tente pedir quantidade superior ao estoque e confira a recusa.
6. Tente acessar a administração sem entrar e confira a solicitação de senha.
7. Registre capturas e resultados para incorporar ao relatório.

## Execução direta do código principal

`python app.py` também funciona. Nesse modo a senha vem de `ADMIN_PASSWORD`,
com o padrão original `troque-esta-senha`. Prefira o iniciador na reunião para
usar a configuração demonstrativa descrita nas instruções.

## Escopo

Demonstração local acadêmica. O servidor não processa pagamentos e o suporte
não é um chat em tempo real. A disponibilização pública exige avaliação própria
de segurança, proteção de dados e infraestrutura.

## Entrega

O código-fonte acompanha este pacote; o relatório PDF é separado.
Preencha nomes e RAs no relatório e disponibilize o código por um link acessível
conforme a orientação da disciplina.
