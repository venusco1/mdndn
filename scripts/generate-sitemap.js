#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const siteDir = path.join(__dirname, '..');
const SITE_URL = (process.env.SITE_URL || 'https://venusco.in').replace(/\/+$/, '');

function escapeXml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function generateSitemap(outputDir = siteDir) {
  const files = fs.readdirSync(siteDir).filter((file) => file.endsWith('.html'));
  const urls = files
    .filter((file) => !/<meta\s+name=["']robots["']\s+content=["'][^"']*noindex/i.test(
      fs.readFileSync(path.join(siteDir, file), 'utf8')
    ))
    .map((file) => {
      const loc = `${SITE_URL}/${file === 'index.html' ? '' : file}`;
      const frequency = file === 'index.html' ? 'weekly' : 'monthly';
      const priority = file === 'index.html' ? '1.0' : '0.8';
      return [
        '  <url>',
        `    <loc>${escapeXml(loc)}</loc>`,
        `    <changefreq>${frequency}</changefreq>`,
        `    <priority>${priority}</priority>`,
        '  </url>'
      ].join('\n');
    });
  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls,
    '</urlset>',
    ''
  ].join('\n');

  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'sitemap.xml'), xml, 'utf8');
  console.log('sitemap.xml generated with', urls.length, 'entries');
  return urls.length;
}

if (require.main === module) generateSitemap();

module.exports = generateSitemap;
