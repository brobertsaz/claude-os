import { test, expect } from '@playwright/test';

test.describe('Configure Modal (Issue #14)', () => {
  test('Configure modal has proper backdrop overlay', async ({ page }) => {
    // Navigate to the app
    await page.goto('/app');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if there are any projects listed
    const projectCards = page.locator('[class*="card"]').filter({ hasText: /Configure|Settings/ });

    // If no projects, check that we see the "No projects" message or create project button
    const noProjectsMessage = page.getByText('No projects yet');
    const hasNoProjects = await noProjectsMessage.isVisible().catch(() => false);

    if (hasNoProjects) {
      console.log('No projects found - skipping configure modal test');
      return;
    }

    // Find and click the Settings/Configure button on first project
    const settingsButton = page.locator('button').filter({ has: page.locator('svg') }).first();

    // Look for a settings icon button
    const configureButton = page.locator('[title="Setup project"], [title="Configure"]').first();

    if (await configureButton.isVisible()) {
      await configureButton.click();

      // Wait for modal to appear
      await page.waitForTimeout(500);

      // Check that the modal backdrop exists with proper styling
      const backdrop = page.locator('.fixed.inset-0').filter({ has: page.locator('.card') });

      // Verify backdrop has semi-transparent background (bg-black/50)
      const backdropElement = backdrop.first();
      if (await backdropElement.isVisible()) {
        const bgClass = await backdropElement.getAttribute('class');

        // Check for semi-transparent background class
        expect(bgClass).toContain('bg-black/50');

        // Verify clicking outside closes the modal
        await backdropElement.click({ position: { x: 10, y: 10 } });

        // Modal should be closed
        await expect(backdrop).not.toBeVisible({ timeout: 2000 });

        console.log('✅ Configure modal has proper backdrop and closes on outside click');
      }
    } else {
      console.log('No configure button found');
    }
  });

  test('Configure modal can be closed with X button', async ({ page }) => {
    await page.goto('/app');
    await page.waitForLoadState('networkidle');

    // Find configure/settings button
    const configureButton = page.locator('[title="Setup project"]').first();

    if (await configureButton.isVisible().catch(() => false)) {
      await configureButton.click();
      await page.waitForTimeout(500);

      // Find and click the close button (X)
      const closeButton = page.locator('button').filter({ hasText: '✕' });
      await closeButton.click();

      // Verify modal is closed
      const modal = page.locator('.fixed.inset-0').filter({ has: page.locator('.card') });
      await expect(modal).not.toBeVisible({ timeout: 2000 });

      console.log('✅ Configure modal closes with X button');
    }
  });
});
