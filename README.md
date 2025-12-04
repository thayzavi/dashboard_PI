🌧️ Dashboard de Monitoramento de Enchentes (IoT + Cloud)

Este projeto implementa um Dashboard em Streamlit para visualização e
análise em tempo real dos dados de um sistema de monitoramento de
enchentes baseado em IoT.

Sensores ultrassônicos enviam dados continuamente para uma API na nuvem,
e o dashboard exibe métricas, gráficos, alertas e logs de auditoria.

Tecnologias Utilizadas

-   Python 3.12
-   Streamlit
-   Altair
-   PyOTP
-   Pandas
-   Requests
-   Pytz
-   python-dotenv

Autenticação

O sistema utiliza: - Login por senha - MFA com Google Authenticator -
Perfis: Gestor e Admin

Variáveis no arquivo .env:

    PASSWORD_GESTOR=suasenha
    PASSWORD_ADMIN=suasenha
    SECRET_KEY=CHAVE_SECRETA_MFA

Funcionalidades

-   Dashboard em tempo real
-   Alertas automáticos (Normal, Médio, Enchente)
-   Gráficos de distância, médias móveis e tendência
-   Tabela de últimas medições
-   Logs de auditoria (apenas admin)

Instalação

1.  Clone o repositório
2.  Crie o arquivo .env
3.  Instale dependências:

    pip install -r requirements.txt

4.  Execute:

    streamlit run app.py

API

-   GET /all → Dados dos sensores
-   GET /logs → Logs de auditoria

Futuras Melhorias

-   Integração com mapas
-   Relatórios em PDF
-   Multi-sensores
