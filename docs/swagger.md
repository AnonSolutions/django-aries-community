## Iniciar o SWAGGER

PORTS="8080:8080 7000:7000" ./run_docker start 
--wallet-type indy \
--seed 000000000000000000000000000Agent \
--wallet-key welldone \
--wallet-name myWallet \
--genesis-url http://172.17.0.1:9000/genesis \
--inbound-transport http 0.0.0.0 8000 \
--outbound-transport http \
--admin 0.0.0.0 8080 \
--admin-insecure-mode \
