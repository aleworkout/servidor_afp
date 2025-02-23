## Configuração do Totem (TV Touch):

    Requisitos:

        Acesso à rede local (via cabo ou Wi-Fi).

        Navegador moderno (Chrome, Firefox) configurado para abrir automaticamente o endereço do servidor.

    Passos:

        No totem, abra o navegador.

        Acesse: http://IP_DO_SERVIDOR:5000 (ex: http://192.168.1.50:5000).

## Fluxo de Funcionamento:

    Cliente no Totem:

        Digita o RUT (com ou sem formatação).

        Clica em "Gerar Certificado".

    Servidor:

        Recebe a solicitação via Flask.

        Abre o Chrome em modo headless.

        Gera o certificado e salva em uploads/.

        Retorna a página de download.

    Totem:

        Exibe o link para download do PDF.
