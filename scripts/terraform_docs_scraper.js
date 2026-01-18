const { chromium } = require('playwright');

const TARGET_URL = 'https://registry.terraform.io/providers/hashicorp/aws/latest/docs';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  try {
    console.log('Navigating to Terraform AWS provider docs...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });

    // Handle cookie consent banner if present
    const acceptButton = page.locator('button:has-text("Accept All")');
    try {
      await acceptButton.waitFor({ state: 'visible', timeout: 3000 });
      await acceptButton.click();
      await page.waitForTimeout(1000);
      console.log('Cookie banner dismissed');
    } catch (e) {
      console.log('No cookie banner or already dismissed');
    }

    // Wait for the docs content
    console.log('Waiting for #provider-docs-content...');
    await page.waitForSelector('#provider-docs-content', { timeout: 10000 });

    // Get the raw HTML
    const html = await page.$eval('#provider-docs-content', el => el.innerHTML);
    require('fs').writeFileSync('/tmp/terraform-aws-docs.html', html);
    console.log('✅ HTML saved to /tmp/terraform-aws-docs.html');

    // Extract and convert to markdown-like format
    const markdown = await page.$eval('#provider-docs-content', el => {
      function processNode(node, depth = 0) {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.textContent;
          if (text.trim()) {
            return text;
          }
          return '';
        }

        if (node.nodeType !== Node.ELEMENT_NODE) return '';

        const tag = node.tagName.toLowerCase();
        let result = '';

        switch (tag) {
          case 'h1':
            result = '\n# ' + node.textContent.trim() + '\n\n';
            break;
          case 'h2':
            result = '\n## ' + node.textContent.trim() + '\n\n';
            break;
          case 'h3':
            result = '\n### ' + node.textContent.trim() + '\n\n';
            break;
          case 'h4':
            result = '\n#### ' + node.textContent.trim() + '\n\n';
            break;
          case 'p':
            result = Array.from(node.childNodes).map(n => processNode(n, depth)).join('') + '\n\n';
            break;
          case 'pre':
            const code = node.textContent.trim();
            result = '\n```\n' + code + '\n```\n\n';
            break;
          case 'code':
            if (node.parentElement?.tagName.toLowerCase() !== 'pre') {
              result = '`' + node.textContent + '`';
            }
            break;
          case 'strong':
          case 'b':
            result = '**' + node.textContent + '**';
            break;
          case 'em':
          case 'i':
            result = '*' + node.textContent + '*';
            break;
          case 'a':
            const href = node.getAttribute('href') || '';
            const text = node.textContent.trim();
            if (href && text) {
              result = '[' + text + '](' + href + ')';
            } else {
              result = text;
            }
            break;
          case 'ul':
            result = '\n' + Array.from(node.children).map(li => '- ' + li.textContent.trim()).join('\n') + '\n\n';
            break;
          case 'ol':
            result = '\n' + Array.from(node.children).map((li, i) => (i + 1) + '. ' + li.textContent.trim()).join('\n') + '\n\n';
            break;
          case 'blockquote':
            result = '\n> ' + node.textContent.trim().replace(/\n/g, '\n> ') + '\n\n';
            break;
          case 'table':
            const rows = Array.from(node.querySelectorAll('tr'));
            if (rows.length > 0) {
              const headerCells = Array.from(rows[0].querySelectorAll('th, td'));
              result = '\n| ' + headerCells.map(c => c.textContent.trim()).join(' | ') + ' |\n';
              result += '| ' + headerCells.map(() => '---').join(' | ') + ' |\n';
              for (let i = 1; i < rows.length; i++) {
                const cells = Array.from(rows[i].querySelectorAll('td'));
                result += '| ' + cells.map(c => c.textContent.trim()).join(' | ') + ' |\n';
              }
              result += '\n';
            }
            break;
          case 'div':
          case 'section':
          case 'article':
            result = Array.from(node.childNodes).map(n => processNode(n, depth)).join('');
            break;
          default:
            if (node.children.length > 0) {
              result = Array.from(node.childNodes).map(n => processNode(n, depth)).join('');
            } else if (node.textContent.trim()) {
              result = node.textContent;
            }
        }

        return result;
      }

      return processNode(el);
    });

    // Clean up the markdown
    const cleanedMarkdown = markdown
      .replace(/\n{3,}/g, '\n\n')
      .replace(/Copy\n/g, '')
      .trim();

    require('fs').writeFileSync('/tmp/terraform-aws-docs.md', cleanedMarkdown);
    console.log('✅ Markdown saved to /tmp/terraform-aws-docs.md');

    console.log('\n--- First 2000 chars of markdown ---\n');
    console.log(cleanedMarkdown.substring(0, 2000));

  } catch (error) {
    console.error('❌ Error:', error.message);
    await page.screenshot({ path: '/tmp/terraform-docs-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
})();
