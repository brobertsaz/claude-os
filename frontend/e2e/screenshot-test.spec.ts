import { test, expect } from '@playwright/test';

test('Take screenshot of configure modal', async ({ page }) => {
  // Navigate to the app
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Take screenshot of projects page
  await page.screenshot({ path: 'e2e/screenshots/projects-page.png', fullPage: true });

  // Click on a project in the sidebar to select it
  const projectItem = page.locator('text=diatrak').first();
  if (await projectItem.isVisible()) {
    await projectItem.click();
    await page.waitForTimeout(1000);

    // Take screenshot after selecting project
    await page.screenshot({ path: 'e2e/screenshots/project-selected.png', fullPage: true });

    // Now look for Configure button
    const configureButton = page.getByRole('button', { name: /Configure/i });
    const configVisible = await configureButton.isVisible().catch(() => false);
    console.log(`Configure button visible: ${configVisible}`);

    if (configVisible) {
      await configureButton.click();
      await page.waitForTimeout(500);

      // Take screenshot of the modal
      await page.screenshot({ path: 'e2e/screenshots/configure-modal.png', fullPage: true });

      // Check if backdrop has correct class
      const backdrop = page.locator('.bg-black\\/50');
      const backdropVisible = await backdrop.isVisible().catch(() => false);
      console.log(`Backdrop with bg-black/50 visible: ${backdropVisible}`);

      expect(backdropVisible).toBe(true);
    } else {
      // Try looking for Settings icon button
      const settingsBtn = page.locator('[title*="Setup"], button:has(svg)').filter({ hasText: '' });
      console.log(`Settings buttons found: ${await settingsBtn.count()}`);
    }
  } else {
    console.log('No project found to click');
  }
});
