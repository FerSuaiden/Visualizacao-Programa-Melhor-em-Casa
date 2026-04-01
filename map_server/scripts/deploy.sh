echo "Deploying application..."

docker build -t registry.simple4decision.com/visualizacao-programa-melhor-em-casa .

docker push registry.simple4decision.com/visualizacao-programa-melhor-em-casa
