pip install poetry || { echo "Failed to install poetry"; exit 1; }

poetry install || { echo "Failed to poetry install"; exit 1; }

cd ./app/server

mkdir -p web || { echo "Failed to create web folder"; exit 1; }

cd ../../web

npm cache clean --force || { echo "Failed to clear npm cache"; exit 1; }

npm install || { echo "npm install failed"; exit 1; }

npm run build || { echo "npm run build failed"; exit 1; }

cp -rf ./dist/* ../app/server/web || { echo "Failed to copy dist contents"; exit 1; }

rm -rf ./dist || { echo "Failed to remove dist directory"; exit 1; }

echo "Build successfully!"