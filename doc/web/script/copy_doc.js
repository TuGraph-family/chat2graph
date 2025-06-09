// Copy directories from source to public directory before build

const fs = require('fs');
const path = require('path');

// Directories to copy from doc/ to public/
const DIRS_TO_COPY = [
  'asset',
  'en-us',
  'zh-cn'
];

const projectRoot = path.resolve(__dirname, '..');
const sourceBaseDir = path.join(projectRoot, '..');
const publicDir = path.join(projectRoot, 'public');

console.log('🚀 Starting pre-build script: Copying assets to /public directory...');

try {
  DIRS_TO_COPY.forEach(dirName => {
    const sourcePath = path.join(sourceBaseDir, dirName);
    const destinationPath = path.join(publicDir, dirName);

    console.log(`\nProcessing directory: "${dirName}"`);

    // Check if source exists
    if (!fs.existsSync(sourcePath)) {
      console.warn(`  ⚠️  Warning: Source directory not found, skipping: ${sourcePath}`);
      return;
    }

    // Clean old directory
    if (fs.existsSync(destinationPath)) {
      console.log(`  - Cleaning up old directory: ${destinationPath}`);
      fs.rmSync(destinationPath, { recursive: true, force: true });
    }

    // Copy directory
    console.log(`  - Copying from "${sourcePath}"`);
    console.log(`    to "${destinationPath}"`);
    fs.cpSync(sourcePath, destinationPath, { recursive: true });

    console.log(`  ✔️  Successfully copied "${dirName}".`);
  });

  console.log('\n✅ Pre-build asset copy finished successfully!');

} catch (error) {
  console.error('\n❌ Fatal error during asset copy process:');
  console.error(error);
  process.exit(1);
}