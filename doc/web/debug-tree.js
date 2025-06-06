const { source, getLanguagePageTree } = require('./lib/source.ts');

console.log('=== Full Page Tree ===');
console.log(JSON.stringify(source.pageTree, null, 2));

console.log('\n=== English Page Tree ===');
console.log(JSON.stringify(getLanguagePageTree('en'), null, 2));

console.log('\n=== Chinese Page Tree ===');
console.log(JSON.stringify(getLanguagePageTree('cn'), null, 2));
