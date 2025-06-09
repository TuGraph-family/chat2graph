// scripts/copy-assets.js
//
// Function: Copy specified directories from source location to `public` directory before build.
// Features:
//   - Automatically handle symlinks (copy actual files that links point to).
//   - Simple configuration, just add directory names to DIRS_TO_COPY array.
//   - Clean old directories before copying to ensure latest content.
//   - Clear logging for easy debugging on platforms like Vercel.

const fs = require('fs');
const path = require('path');

// --- Configuration Center ---
// Add all folder names that need to be copied from `doc/` directory to `public/` directory in this array.
const DIRS_TO_COPY = [
  'asset',
  'en-us',
  'zh-cn'
];
// --- Configuration End ---

const projectRoot = path.resolve(__dirname, '..');
const sourceBaseDir = path.join(projectRoot, '..');
const publicDir = path.join(projectRoot, 'public');

console.log('🚀 Starting pre-build script: Copying assets to /public directory...');

try {
  DIRS_TO_COPY.forEach(dirName => {
    const sourcePath = path.join(sourceBaseDir, dirName);
    const destinationPath = path.join(publicDir, dirName);

    console.log(`\nProcessing directory: "${dirName}"`);

    // 1. Check if source directory exists, skip with warning if not found
    if (!fs.existsSync(sourcePath)) {
      console.warn(`  ⚠️  Warning: Source directory not found, skipping: ${sourcePath}`);
      return; // Skip to next directory to copy
    }

    // 2. Clean up old version in `public` directory to ensure fresh copy
    if (fs.existsSync(destinationPath)) {
      console.log(`  - Cleaning up old directory: ${destinationPath}`);
      fs.rmSync(destinationPath, { recursive: true, force: true });
    }

    // 3. Recursively copy entire directory.
    //    fs.cpSync will automatically resolve symlinks and copy the actual files/directories they point to.
    console.log(`  - Copying from "${sourcePath}"`);
    console.log(`    to "${destinationPath}"`);
    fs.cpSync(sourcePath, destinationPath, { recursive: true });

    console.log(`  ✔️  Successfully copied "${dirName}".`);
  });

  console.log('\n✅ Pre-build asset copy finished successfully!');

} catch (error) {
  console.error('\n❌ Fatal error during asset copy process:');
  console.error(error);
  // Exit with error code, this will cause Vercel build to fail so you can discover issues promptly.
  process.exit(1);
}