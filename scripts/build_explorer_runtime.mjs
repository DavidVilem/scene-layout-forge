// Development-only reproducible build. End users need neither npm nor an Internet connection.
// Install dependencies from assets/explorer/package.json in a separate development workspace.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,copyFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtime=process.argv[2];if(!runtime)throw Error('Pass a development workspace containing node_modules');
const require=createRequire(path.join(path.resolve(runtime),'package.json'));
const esbuild=require('esbuild'),threePackage=JSON.parse(readFileSync(path.join(runtime,'node_modules/three/package.json'),'utf8'));
if(threePackage.version!=='0.187.0')throw Error('Expected Three.js 0.187.0');
await esbuild.build({entryPoints:[path.join(root,'assets/explorer/viewer.mjs')],bundle:true,minify:true,format:'iife',target:'es2020',
 outfile:path.join(root,'assets/explorer/explorer.bundle.js'),nodePaths:[path.join(path.resolve(runtime),'node_modules')],legalComments:'inline'});
copyFileSync(path.join(runtime,'node_modules/three/LICENSE'),path.join(root,'assets/explorer/THREE-LICENSE.txt'));
