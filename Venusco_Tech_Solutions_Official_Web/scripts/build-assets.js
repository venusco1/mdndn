#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const generateSitemap = require('./generate-sitemap');

const siteDir = path.join(__dirname, '..');
const outDir = path.join(siteDir, 'dist');
const staticFiles = ['robots.txt', '_headers', '_redirects'];

function copyDirectory(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) copyDirectory(sourcePath, destinationPath);
    else if (entry.isFile()) fs.copyFileSync(sourcePath, destinationPath);
  }
}

function build() {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  for (const file of fs.readdirSync(siteDir)) {
    if (file.endsWith('.html')) {
      fs.copyFileSync(path.join(siteDir, file), path.join(outDir, file));
    }
  }
  copyDirectory(path.join(siteDir, 'assets'), path.join(outDir, 'assets'));
  staticFiles.forEach((file) => {
    const source = path.join(siteDir, file);
    if (fs.existsSync(source)) fs.copyFileSync(source, path.join(outDir, file));
  });

  const sitemapEntries = generateSitemap(outDir);
  console.log(`Build completed. Deploy the contents of ${outDir} (${sitemapEntries} sitemap entries).`);
}

try {
  build();
} catch (error) {
  console.error('Build failed:', error);
  process.exitCode = 1;
}
