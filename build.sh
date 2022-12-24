docker buildx rm mybuilder
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name mybuilder --driver docker-container --bootstrap
docker buildx use mybuilder
docker buildx build --platform linux/amd64,linux/arm64 -t yvguim/mysafeip:0.9 --push .
