Sockets
Este projeto demonstra o uso de sockets em Python para comunicação entre cliente e servidor em uma rede. Ele simula a troca de pacotes com controle de integridade, usando técnicas como soma de verificação (checksum), controle de sequência e reconhecimento de pacotes.

Funcionalidades
Conexão Cliente-Servidor: Estabelece uma conexão entre cliente e servidor usando sockets TCP.
Controle de Integridade: Implementa soma de verificação para garantir que os dados sejam transmitidos sem erros.
Reconhecimento Positivo e Negativo: O servidor responde com ACK para pacotes válidos e NACK para pacotes corrompidos.
Controle de Sequência e Janela: Suporte para controle de sequência de pacotes e janela deslizante.
Como Usar
Execute o servidor: python server.py.
Em outro terminal, execute o cliente: python client.py.
Acompanhe o envio e recebimento de pacotes e verifique os logs para mensagens de ACK e NACK.
Esse README resume o projeto e explica suas principais funcionalidades e como executá-lo.
