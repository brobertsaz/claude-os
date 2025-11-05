/**
 * Claude OS Screenshot Capture Script
 *
 * Automatically captures beautiful screenshots of the entire Claude OS interface
 * using Playwright for documentation and marketing materials.
 *
 * Usage:
 *   node scripts/capture-screenshots.js
 *
 * Prerequisites:
 *   - Frontend running on http://localhost:5173
 *   - MCP server running on http://localhost:8051
 *   - At least one project created (e.g., Pistn)
 */

const { chromium } = require(require('path').join(__dirname, '../frontend/node_modules/playwright'));
const path = require('path');
const fs = require('fs');

// Configuration
const BASE_URL = 'http://localhost:5173';
const SCREENSHOTS_DIR = path.join(__dirname, '../frontend/public/assets/screenshots');
const VIEWPORT = { width: 1920, height: 1080 };
const WAIT_TIME = 2000; // Wait for animations/data loading

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function captureScreenshots() {
  console.log('🎭 Starting Claude OS screenshot capture...\n');

  const browser = await chromium.launch({
    headless: false, // Set to true for CI/CD
  });

  const context = await browser.newContext({
    viewport: VIEWPORT,
  });

  const page = await context.newPage();

  try {
    // 1. Welcome Screen
    console.log('📸 Capturing: Welcome Screen...');
    await page.goto(BASE_URL);
    await page.waitForTimeout(WAIT_TIME);
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'welcome-screen.png'),
      fullPage: false,
    });
    console.log('✅ Saved: welcome-screen.png\n');

    // Navigate to app
    await page.click('a[href="/app"]');
    await page.waitForTimeout(WAIT_TIME);

    // 2. Projects List
    console.log('📸 Capturing: Projects List...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'projects-list-page.png'),
      fullPage: false,
    });
    console.log('✅ Saved: projects-list-page.png\n');

    // Select first project (Pistn)
    const firstProject = await page.locator('.p-3.rounded-lg.border').first();
    await firstProject.click();
    await page.waitForTimeout(WAIT_TIME);

    // 3. Project Overview
    console.log('📸 Capturing: Project Overview...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'project-overview-page.png'),
      fullPage: false,
    });
    console.log('✅ Saved: project-overview-page.png\n');

    // 4. Kanban Board
    console.log('📸 Capturing: Kanban Board...');
    await page.click('button:has-text("Kanban Board")');
    await page.waitForTimeout(WAIT_TIME + 1000); // Extra time for Kanban data load
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'project-kanban-page.png'),
      fullPage: true, // Capture full Kanban board
    });
    console.log('✅ Saved: project-kanban-page.png\n');

    // 5. Kanban - Task Detail Modal (if tasks exist)
    try {
      console.log('📸 Capturing: Task Detail Modal...');
      const taskCard = await page.locator('.bg-cool-blue\\/10.border').first();
      await taskCard.click();
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'kanban-task-detail-modal.png'),
        fullPage: false,
      });
      console.log('✅ Saved: kanban-task-detail-modal.png\n');

      // Close modal
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    } catch (e) {
      console.log('⚠️  No tasks found for task detail screenshot\n');
    }

    // 6. MCP Management
    console.log('📸 Capturing: MCP Management...');
    await page.click('button:has-text("MCP Management")');
    await page.waitForTimeout(WAIT_TIME);

    // Click on first MCP in sidebar
    const firstMCP = await page.locator('.p-2.rounded.border.text-sm').first();
    await firstMCP.click();
    await page.waitForTimeout(WAIT_TIME);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'project-mcp-page.png'),
      fullPage: false,
    });
    console.log('✅ Saved: project-mcp-page.png\n');

    // 7. Chat Interface
    console.log('📸 Capturing: Chat Interface...');
    await page.click('button:has-text("Chat")');
    await page.waitForTimeout(WAIT_TIME);
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'project-chat-page.png'),
      fullPage: false,
    });
    console.log('✅ Saved: project-chat-page.png\n');

    // 8. Services Dashboard
    console.log('📸 Capturing: Services Dashboard...');
    await page.click('button:has-text("Services")');
    await page.waitForTimeout(WAIT_TIME);
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'project-services-dashboard-page.png'),
      fullPage: false,
    });
    console.log('✅ Saved: project-services-dashboard-page.png\n');

    // Bonus: Mobile screenshots (optional)
    console.log('📱 Capturing mobile screenshots...');
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X

    await page.goto(BASE_URL);
    await page.waitForTimeout(WAIT_TIME);
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'mobile-welcome-screen.png'),
      fullPage: false,
    });
    console.log('✅ Saved: mobile-welcome-screen.png\n');

    console.log('✨ All screenshots captured successfully!\n');
    console.log(`📁 Screenshots saved to: ${SCREENSHOTS_DIR}\n`);

  } catch (error) {
    console.error('❌ Error capturing screenshots:', error);
  } finally {
    await browser.close();
  }
}

// Run the script
captureScreenshots().catch(console.error);
