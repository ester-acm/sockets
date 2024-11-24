# Sockets - protocolo de comunicação cliente-servidor

Este projeto demonstra o uso de sockets em Python para comunicação entre cliente e servidor em uma rede. Ele implementa um protocolo de aplicação personalizado para troca confiável de pacotes, utilizando técnicas como soma de verificação (checksum), controle de sequência, janela deslizante e reconhecimento de pacotes.

## Funcionalidades

- Conexão cliente-servidor: Estabelece uma conexão entre cliente e servidor usando sockets TCP.
- Controle de integridade: Implementa soma de verificação para garantir que os dados sejam transmitidos sem erros.
- Reconhecimento positivo e negativo: O servidor responde com ACK para pacotes válidos e NACK para pacotes corrompidos.
- Controle de sequência e janela: Suporte para controle de sequência de pacotes e janela deslizante.
- Simulação de erros: Capacidade de simular falhas de integridade e perdas de pacotes.

## Como usar

1. Execute o servidor: `python server.py`
2. Em outro terminal, execute o cliente: `python client.py`
3. Acompanhe o envio e recebimento de pacotes e verifique os logs para mensagens de ACK e NACK.

## Protocolo de aplicação

O protocolo de aplicação implementado neste projeto define as regras para a comunicação entre cliente e servidor. Abaixo está uma descrição formal do protocolo:

### Formato dos pacotes

1. **Pacote de dados (cliente para servidor)** 

Formato: `seq_num:checksum:payload`
   - `seq_num`: Número de sequência do pacote (inteiro)
   - `checksum`: Soma de verificação MD5 do payload
   - `payload`: Dados do pacote

3. **Pacote de reconhecimento (servidor para cliente)**

Formato: `ACK:seq_num` ou `NACK:seq_num`
   - `ACK`: Reconhecimento positivo
   - `NACK`: Reconhecimento negativo
   - `seq_num`: Número de sequência do pacote reconhecido

### Fluxo de comunicação

1. **Inicialização**
   - O cliente estabelece uma conexão TCP com o servidor.
   - O cliente inicializa sua janela de envio e número de sequência.

2. **Envio de dados**
   - O cliente envia pacotes dentro da janela atual.
   - Cada pacote inclui número de sequência, checksum e payload.

3. **Recebimento e verificação (servidor)**
   - O servidor recebe o pacote e verifica a integridade usando o checksum.
   - Se a integridade for válida e o número de sequência for o esperado, o servidor processa o pacote.

4. **Reconhecimento**
   - Para pacotes válidos, o servidor envia um ACK.
   - Para pacotes inválidos ou fora de ordem, o servidor envia um NACK.

5. **Tratamento de erros**
   - Se o cliente receber um NACK ou não receber resposta (timeout), ele retransmite o pacote.
   - O servidor armazena pacotes fora de ordem em um buffer para processamento posterior.

6. **Controle de fluxo**
   - O cliente ajusta dinamicamente o tamanho da janela de envio com base nos ACKs recebidos.
   - A janela aumenta para ACKs consecutivos e diminui em caso de perdas ou timeouts.

### Características adicionais

- **Simulação de erros**: O cliente pode simular erros de integridade enviando 'erro' ao invés de um pacote válido.
- **Perda de ACK**: O servidor pode simular a perda de ACKs para pacotes específicos.
- **Timeout**: Um temporizador é usado para detectar pacotes perdidos e iniciar retransmissões.

Este protocolo fornece uma comunicação confiável entre cliente e servidor, lidando com diversos cenários de erro e otimizando o fluxo de dados através do controle dinâmico da janela de transmissão.
