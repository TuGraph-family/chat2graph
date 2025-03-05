# install dependencies
pip install poetry || { echo "Failed to install poetry"; }
poetry lock || { echo "Failed to update lock file"; }
poetry install || { echo "Failed to poetry install"; }

# prepare target directory
cd ./app || { echo "Failed to change to app directory"; return 1; }
mkdir -p server/web || { echo "Failed to create server/web folder"; }

# build web assets
cd ../web || { echo "Failed to change to web directory"; return 1; }
npm cache clean --force || { echo "Failed to clear npm cache"; }
npm install || { echo "npm install failed"; }
npm run build || { echo "npm run build failed"; }

# copy build artifacts
cp -rf ./dist/* ../app/server/web || { echo "Failed to copy dist contents"; }
rm -rf ./dist || { echo "Failed to remove dist directory"; }

# return to root directory
cd ..
echo "Build successful!"